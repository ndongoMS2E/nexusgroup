"""
NEXUS GROUP - Documents Endpoints
==================================
Gestion des documents avec contrôle d'accès par rôle

Permissions:
- Admin Général: CRUD total + validation pour client
- Admin Chantier: Upload/voir/supprimer ses chantiers + valider pour client
- Comptable: Voir documents techniques (factures, bons) + télécharger
- Chef Chantier: Upload photos/vidéos/docs de son chantier
- Magasinier: Upload bons de livraison
- Direction: Lecture seule tous documents
- Ouvrier: ❌ Pas d'accès aux documents sensibles
- Client: Voir/télécharger UNIQUEMENT les documents validés pour lui
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_admin,
    require_roles,
    has_permission
)
from app.models.document import Document
from app.models.chantier import Chantier

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "/app/uploads"


# =============================================================================
# TYPES DE DOCUMENTS
# =============================================================================

class DocumentType:
    # Documents techniques
    PLAN = "plan"
    DEVIS = "devis"
    CONTRAT = "contrat"
    RAPPORT = "rapport"
    FACTURE = "facture"
    BON_LIVRAISON = "bon_livraison"
    
    # Médias
    PHOTO = "photo"
    VIDEO = "video"
    
    # Autres
    PERMIS = "permis"
    AUTRE = "autre"
    
    @classmethod
    def all_types(cls):
        return [
            cls.PLAN, cls.DEVIS, cls.CONTRAT, cls.RAPPORT,
            cls.FACTURE, cls.BON_LIVRAISON, cls.PHOTO, cls.VIDEO,
            cls.PERMIS, cls.AUTRE
        ]
    
    @classmethod
    def types_comptable(cls):
        """Types accessibles au comptable"""
        return [cls.FACTURE, cls.BON_LIVRAISON, cls.DEVIS, cls.CONTRAT]


# =============================================================================
# SCHÉMAS
# =============================================================================

class DocumentResponse(BaseModel):
    id: int
    nom: str
    type_document: str
    taille: int
    description: Optional[str]
    chantier_id: int
    valide_client: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# UPLOAD DE DOCUMENT
# =============================================================================

@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    chantier_id: int = Form(...),
    type_document: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("upload_document"))
):
    """
    Uploader un document
    
    Permissions:
    - Admin Général: Tous les chantiers
    - Admin Chantier: Ses chantiers assignés
    - Chef Chantier: Son chantier seulement
    - Magasinier: Bons de livraison seulement
    - Autres: ❌ Pas d'upload
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Vérifier que le chantier existe
    result = await db.execute(select(Chantier).where(Chantier.id == chantier_id))
    chantier = result.scalar_one_or_none()
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier l'accès au chantier
    if role != RoleEnum.ADMIN_GENERAL:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Magasinier: limité aux bons de livraison
    if role == RoleEnum.MAGASINIER:
        if type_document not in [DocumentType.BON_LIVRAISON, DocumentType.PHOTO]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez uploader que des bons de livraison ou photos"
            )
    
    # Vérifier le type de document
    if type_document not in DocumentType.all_types():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de document invalide. Types autorisés: {', '.join(DocumentType.all_types())}"
        )
    
    # Vérifier le type de fichier
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.mp4', '.mov', '.avi']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Type de fichier non autorisé. Extensions autorisées: {', '.join(allowed_extensions)}"
        )
    
    # Vérifier la taille (max 50 MB)
    content = await file.read()
    max_size = 50 * 1024 * 1024  # 50 MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux. Taille maximale: 50 MB"
        )
    
    # Générer un nom unique
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    # Créer le dossier si nécessaire
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Sauvegarder le fichier
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Enregistrer en DB
    document = Document(
        nom=file.filename,
        type_document=type_document,
        fichier_path=unique_name,
        taille=len(content),
        description=description,
        chantier_id=chantier_id,
        uploaded_by=user_id,
        valide_client=False  # Par défaut non visible par le client
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return {
        "id": document.id,
        "nom": document.nom,
        "type_document": document.type_document,
        "taille": document.taille,
        "valide_client": document.valide_client,
        "message": "Document uploadé avec succès"
    }


# =============================================================================
# LISTE DES DOCUMENTS
# =============================================================================

@router.get("/", response_model=List[dict])
async def list_documents(
    chantier_id: Optional[int] = Query(None, description="Filtrer par chantier"),
    type_document: Optional[str] = Query(None, description="Filtrer par type"),
    valide_client: Optional[bool] = Query(None, description="Filtrer par validation client"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_documents"))
):
    """
    Liste des documents selon le rôle:
    
    - Admin Général, Direction: Tous les documents
    - Admin Chantier, Chef Chantier: Documents de leurs chantiers
    - Comptable: Documents techniques (factures, bons, devis, contrats)
    - Magasinier: Documents de stock (bons de livraison)
    - Client: UNIQUEMENT les documents validés pour lui
    - Ouvrier: ❌ Pas d'accès
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id")
    chantiers_assignes = user.get("chantiers_assignes", [])
    user_chantier_id = user.get("chantier_id")
    
    query = select(Document)
    
    # === FILTRAGE PAR RÔLE ===
    
    # Client: uniquement documents validés de son chantier
    if role == RoleEnum.CLIENT:
        query = query.where(Document.valide_client == True)
        # TODO: Filtrer par chantier du client
        # query = query.where(Document.chantier_id == user_chantier_client)
    
    # Comptable: documents techniques seulement
    elif role == RoleEnum.COMPTABLE:
        query = query.where(Document.type_document.in_(DocumentType.types_comptable()))
    
    # Magasinier: bons de livraison seulement
    elif role == RoleEnum.MAGASINIER:
        query = query.where(Document.type_document == DocumentType.BON_LIVRAISON)
    
    # Admin Chantier, Chef Chantier: leurs chantiers
    elif role in [RoleEnum.ADMIN_CHANTIER, RoleEnum.CHEF_CHANTIER]:
        if chantiers_assignes:
            query = query.where(Document.chantier_id.in_(chantiers_assignes))
        elif user_chantier_id:
            query = query.where(Document.chantier_id == user_chantier_id)
    
    # Admin Général, Direction: tous les documents (pas de filtre)
    
    # === FILTRES ADDITIONNELS ===
    
    if chantier_id:
        # Vérifier l'accès au chantier demandé
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION]:
            if role == RoleEnum.COMPTABLE:
                pass  # Comptable peut voir tous les chantiers (docs techniques)
            elif not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès aux documents de ce chantier"
                )
        query = query.where(Document.chantier_id == chantier_id)
    
    if type_document:
        query = query.where(Document.type_document == type_document)
    
    if valide_client is not None:
        query = query.where(Document.valide_client == valide_client)
    
    query = query.order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [{
        "id": d.id,
        "nom": d.nom,
        "type_document": d.type_document,
        "taille": d.taille,
        "description": d.description,
        "chantier_id": d.chantier_id,
        "valide_client": d.valide_client,
        "uploaded_by": d.uploaded_by,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in documents]


# =============================================================================
# TÉLÉCHARGER UN DOCUMENT
# =============================================================================

@router.get("/download/{document_id}")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("download_document"))
):
    """
    Télécharger un document
    
    - Client: Uniquement si le document est validé pour lui
    - Autres: Selon accès au chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document non trouvé"
        )
    
    # Client: vérifier que le document est validé
    if role == RoleEnum.CLIENT:
        if not document.valide_client:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ce document n'est pas accessible"
            )
    
    # Vérifier l'accès au chantier
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, RoleEnum.CLIENT]:
        # Comptable: accès aux documents techniques de tous les chantiers
        if role == RoleEnum.COMPTABLE:
            if document.type_document not in DocumentType.types_comptable():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez accès qu'aux documents financiers"
                )
        elif not has_chantier_access(user, document.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce document"
            )
    
    file_path = os.path.join(UPLOAD_DIR, document.fichier_path)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Fichier non trouvé sur le serveur"
        )
    
    # TODO: Logger le téléchargement pour audit
    # await log_audit(db, user, "download_document", document.id)
    
    return FileResponse(
        file_path,
        filename=document.nom,
        media_type="application/octet-stream"
    )


# =============================================================================
# VALIDER UN DOCUMENT POUR LE CLIENT
# =============================================================================

@router.put("/{document_id}/validate-client")
async def validate_document_for_client(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("validate_document_client"))
):
    """
    Valider un document pour qu'il soit visible par le client
    
    ⚠️ SÉCURITÉ: Admin Général et Admin Chantier seulement
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document non trouvé"
        )
    
    # Admin Chantier: vérifier l'accès au chantier
    if role == RoleEnum.ADMIN_CHANTIER:
        if not has_chantier_access(user, document.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    document.valide_client = True
    document.validated_client_by = user_id
    document.validated_client_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Document validé pour le client",
        "document_id": document.id,
        "nom": document.nom
    }


# =============================================================================
# RETIRER LA VALIDATION CLIENT
# =============================================================================

@router.put("/{document_id}/unvalidate-client")
async def unvalidate_document_for_client(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("validate_document_client"))
):
    """
    Retirer la validation client d'un document
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document non trouvé"
        )
    
    # Admin Chantier: vérifier l'accès au chantier
    if role == RoleEnum.ADMIN_CHANTIER:
        if not has_chantier_access(user, document.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    document.valide_client = False
    
    await db.commit()
    
    return {
        "message": "Validation client retirée",
        "document_id": document.id
    }


# =============================================================================
# SUPPRIMER UN DOCUMENT
# =============================================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("delete_document"))
):
    """
    Supprimer un document
    
    Permissions:
    - Admin Général: Peut tout supprimer
    - Admin Chantier: Documents de ses chantiers
    - Direction: ❌ Lecture seule
    - Autres: ❌ Pas de suppression
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Direction ne peut pas supprimer
    if role == RoleEnum.DIRECTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le rôle Direction est en lecture seule"
        )
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document non trouvé"
        )
    
    # Admin Chantier: vérifier l'accès
    if role == RoleEnum.ADMIN_CHANTIER:
        if not has_chantier_access(user, document.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # TODO: Logger pour audit AVANT suppression
    # await log_audit(db, user, "delete_document", document.id, {"nom": document.nom})
    
    # Supprimer le fichier physique
    file_path = os.path.join(UPLOAD_DIR, document.fichier_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    await db.delete(document)
    await db.commit()
    
    return {"message": f"Document '{document.nom}' supprimé"}


# =============================================================================
# DOCUMENTS VALIDÉS POUR LE CLIENT (Vue Client)
# =============================================================================

@router.get("/client/validated")
async def list_client_validated_documents(
    chantier_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_documents_valides"))
):
    """
    Liste des documents validés pour le client
    
    Vue spéciale pour le rôle Client
    """
    
    query = select(Document).where(
        Document.chantier_id == chantier_id,
        Document.valide_client == True
    ).order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [{
        "id": d.id,
        "nom": d.nom,
        "type_document": d.type_document,
        "description": d.description,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in documents]


# =============================================================================
# STATISTIQUES DES DOCUMENTS
# =============================================================================

@router.get("/stats")
async def get_documents_stats(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_documents"))
):
    """
    Statistiques des documents
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(Document)
    
    if chantier_id:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
        query = query.where(Document.chantier_id == chantier_id)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Stats par type
    par_type = {}
    for d in documents:
        t = d.type_document or "Autre"
        if t not in par_type:
            par_type[t] = {"count": 0, "taille_totale": 0}
        par_type[t]["count"] += 1
        par_type[t]["taille_totale"] += d.taille or 0
    
    # Stats validation client
    valides_client = len([d for d in documents if d.valide_client])
    
    return {
        "total_documents": len(documents),
        "taille_totale": sum(d.taille or 0 for d in documents),
        "valides_client": valides_client,
        "non_valides_client": len(documents) - valides_client,
        "par_type": par_type
    }


# =============================================================================
# LISTE DES TYPES DE DOCUMENTS
# =============================================================================

@router.get("/types")
async def list_document_types(user: dict = Depends(get_current_user)):
    """
    Liste des types de documents disponibles
    """
    return {
        "types": DocumentType.all_types(),
        "types_comptable": DocumentType.types_comptable()
    }