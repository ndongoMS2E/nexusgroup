"""
NEXUS GROUP - Dépenses Endpoints
=================================
Gestion des dépenses avec contrôle d'accès par rôle

Workflow de validation:
1. Chef Chantier crée une dépense (status: "en_attente")
2. Admin Chantier peut valider niveau chantier (optionnel)
3. Admin Général valide définitivement (status: "approuvee")

Permissions:
- Admin Général: CRUD total + validation finale
- Admin Chantier: Voir ses chantiers + valider niveau chantier
- Comptable: Voir toutes + créer + approuver
- Chef Chantier: Voir/créer pour son chantier seulement
- Direction: Lecture seule toutes les dépenses
- Magasinier: ❌ Pas d'accès
- Ouvrier: ❌ Pas d'accès
- Client: ❌ Pas d'accès aux budgets internes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime, date

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_roles,
    require_admin,
    require_not_read_only,
    has_permission,
    DataFilter
)
from app.models.depense import Depense
from app.models.chantier import Chantier
from app.schemas.depense import DepenseCreate, DepenseResponse

router = APIRouter(prefix="/depenses", tags=["Depenses"])


# =============================================================================
# SCHÉMAS ADDITIONNELS
# =============================================================================

class DepenseUpdate(BaseModel):
    libelle: Optional[str] = None
    description: Optional[str] = None
    categorie: Optional[str] = None
    montant: Optional[float] = None
    date_depense: Optional[date] = None
    fournisseur: Optional[str] = None


class DepenseReject(BaseModel):
    motif: str


class DepenseStats(BaseModel):
    total_depenses: float
    nb_depenses: int
    en_attente: int
    approuvees: int
    rejetees: int


# =============================================================================
# STATUTS DES DÉPENSES
# =============================================================================

class DepenseStatus:
    EN_ATTENTE = "en_attente"
    VALIDEE_CHANTIER = "validee_chantier"  # Validée par Admin Chantier
    APPROUVEE = "approuvee"                 # Validée par Admin Général
    REJETEE = "rejetee"
    ANNULEE = "annulee"


# =============================================================================
# LISTE DES DÉPENSES
# =============================================================================

@router.get("/", response_model=List[DepenseResponse])
async def list_depenses(
    chantier_id: Optional[int] = Query(None, description="Filtrer par chantier"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    date_debut: Optional[date] = Query(None, description="Date de début"),
    date_fin: Optional[date] = Query(None, description="Date de fin"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_depenses"))
):
    """
    Liste des dépenses selon le rôle:
    
    - Admin Général, Comptable, Direction: Toutes les dépenses
    - Admin Chantier: Dépenses de ses chantiers
    - Chef Chantier: Dépenses de son chantier seulement
    - Autres: ❌ Pas d'accès
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_chantier_id = user.get("chantier_id")
    chantiers_assignes = user.get("chantiers_assignes", [])
    
    query = select(Depense)
    
    # Filtrage par rôle
    if role == RoleEnum.CHEF_CHANTIER:
        # Chef chantier: seulement son chantier
        if user_chantier_id:
            query = query.where(Depense.chantier_id == user_chantier_id)
        elif chantiers_assignes:
            query = query.where(Depense.chantier_id.in_(chantiers_assignes))
        else:
            return []  # Pas de chantier assigné
    
    elif role == RoleEnum.ADMIN_CHANTIER:
        # Admin chantier: ses chantiers assignés
        if chantiers_assignes:
            query = query.where(Depense.chantier_id.in_(chantiers_assignes))
        elif user_chantier_id:
            query = query.where(Depense.chantier_id == user_chantier_id)
    
    # Sinon (Admin, Comptable, Direction): toutes les dépenses
    
    # Filtres additionnels
    if chantier_id:
        # Vérifier l'accès au chantier demandé
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
            if chantier_id not in chantiers_assignes and chantier_id != user_chantier_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès aux dépenses de ce chantier"
                )
        query = query.where(Depense.chantier_id == chantier_id)
    
    if status:
        query = query.where(Depense.status == status)
    
    if date_debut:
        query = query.where(Depense.date_depense >= date_debut)
    
    if date_fin:
        query = query.where(Depense.date_depense <= date_fin)
    
    query = query.order_by(Depense.created_at.desc())
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# CRÉER UNE DÉPENSE
# =============================================================================

@router.post("/", response_model=DepenseResponse)
async def create_depense(
    data: DepenseCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("create_depense"))
):
    """
    Créer une nouvelle dépense
    
    - Admin Général: Peut créer pour n'importe quel chantier
    - Comptable: Peut créer pour n'importe quel chantier
    - Chef Chantier: Peut créer UNIQUEMENT pour son chantier
    
    La dépense est créée avec le statut "en_attente" et doit être approuvée
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    user_chantier_id = user.get("chantier_id")
    chantiers_assignes = user.get("chantiers_assignes", [])
    
    # Vérifier que le chantier existe
    result = await db.execute(select(Chantier).where(Chantier.id == data.chantier_id))
    chantier = result.scalar_one_or_none()
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier l'accès au chantier pour Chef Chantier
    if role == RoleEnum.CHEF_CHANTIER:
        can_access = (
            data.chantier_id == user_chantier_id or 
            data.chantier_id in chantiers_assignes
        )
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Vous ne pouvez créer des dépenses que pour votre chantier"
            )
    
    # Générer une référence unique
    reference = f"DEP-{datetime.now().strftime('%Y%m')}-{random.randint(1000,9999)}"
    
    # Vérifier unicité de la référence
    result = await db.execute(select(Depense).where(Depense.reference == reference))
    while result.scalar_one_or_none():
        reference = f"DEP-{datetime.now().strftime('%Y%m')}-{random.randint(1000,9999)}"
        result = await db.execute(select(Depense).where(Depense.reference == reference))
    
    # Créer la dépense
    depense = Depense(
        reference=reference,
        libelle=data.libelle,
        description=data.description,
        categorie=data.categorie,
        montant=data.montant,
        date_depense=data.date_depense,
        fournisseur=data.fournisseur,
        chantier_id=data.chantier_id,
        status=DepenseStatus.EN_ATTENTE,
        created_by=user_id
    )
    
    db.add(depense)
    await db.commit()
    await db.refresh(depense)
    
    # TODO: Notifier les admins qu'une dépense est en attente
    # await notify_admins_new_depense(db, depense)
    
    return depense


# =============================================================================
# DÉTAIL D'UNE DÉPENSE
# =============================================================================

@router.get("/{id}", response_model=DepenseResponse)
async def get_depense(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_depenses"))
):
    """
    Récupérer les détails d'une dépense
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    # Vérifier l'accès au chantier de la dépense
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
        if not has_chantier_access(user, depense.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à cette dépense"
            )
    
    return depense


# =============================================================================
# MODIFIER UNE DÉPENSE (avant approbation)
# =============================================================================

@router.put("/{id}", response_model=DepenseResponse)
async def update_depense(
    id: int,
    data: DepenseUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("create_depense"))
):
    """
    Modifier une dépense
    
    ⚠️ Seules les dépenses "en_attente" peuvent être modifiées
    - Le créateur peut modifier sa propre dépense
    - Admin peut modifier toutes les dépenses en attente
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    # Vérifier que la dépense est encore modifiable
    if depense.status != DepenseStatus.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de modifier une dépense avec le statut '{depense.status}'"
        )
    
    # Vérifier les droits de modification
    if role != RoleEnum.ADMIN_GENERAL:
        # Seul le créateur ou un admin peut modifier
        if depense.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez modifier que vos propres dépenses"
            )
    
    # Mettre à jour
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(depense, field, value)
    
    depense.updated_at = datetime.utcnow()
    depense.updated_by = user_id
    
    await db.commit()
    await db.refresh(depense)
    
    return depense


# =============================================================================
# VALIDER UNE DÉPENSE (Admin Chantier - niveau intermédiaire)
# =============================================================================

@router.put("/{id}/validate-chantier")
async def validate_depense_chantier(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("validate_commande_chantier"))
):
    """
    Validation intermédiaire par l'Admin Chantier
    
    Passe le statut de "en_attente" à "validee_chantier"
    L'Admin Général doit encore approuver définitivement
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    # Vérifier le statut
    if depense.status != DepenseStatus.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cette dépense ne peut pas être validée (statut: {depense.status})"
        )
    
    # Vérifier l'accès au chantier
    if role == RoleEnum.ADMIN_CHANTIER:
        if not has_chantier_access(user, depense.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Valider
    depense.status = DepenseStatus.VALIDEE_CHANTIER
    depense.validated_chantier_by = user_id
    depense.validated_chantier_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": "Dépense validée au niveau chantier",
        "status": depense.status,
        "next_step": "Approbation finale par l'Administrateur Général"
    }


# =============================================================================
# APPROUVER UNE DÉPENSE (Validation finale - Admin Général)
# =============================================================================

@router.put("/{id}/approve")
async def approve_depense(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin Général seulement
):
    """
    Approbation finale d'une dépense
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut approuver définitivement
    
    - Met à jour le statut à "approuvee"
    - Ajoute le montant au budget consommé du chantier
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    # Vérifier le statut
    if depense.status == DepenseStatus.APPROUVEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette dépense est déjà approuvée"
        )
    
    if depense.status == DepenseStatus.REJETEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'approuver une dépense rejetée"
        )
    
    # Approuver
    depense.status = DepenseStatus.APPROUVEE
    depense.approved_by = user_id
    depense.approved_at = datetime.utcnow()
    
    # Mettre à jour le budget consommé du chantier
    result = await db.execute(select(Chantier).where(Chantier.id == depense.chantier_id))
    chantier = result.scalar_one_or_none()
    if chantier:
        if chantier.budget_consomme is None:
            chantier.budget_consomme = 0
        chantier.budget_consomme += depense.montant
    
    await db.commit()
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "approve_depense", depense.id, {"montant": depense.montant})
    
    return {
        "message": "Dépense approuvée",
        "reference": depense.reference,
        "montant": depense.montant,
        "status": depense.status
    }


# =============================================================================
# REJETER UNE DÉPENSE
# =============================================================================

@router.put("/{id}/reject")
async def reject_depense(
    id: int,
    data: DepenseReject,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Rejeter une dépense
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut rejeter
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    if depense.status == DepenseStatus.APPROUVEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de rejeter une dépense déjà approuvée"
        )
    
    depense.status = DepenseStatus.REJETEE
    depense.rejected_by = user_id
    depense.rejected_at = datetime.utcnow()
    depense.motif_rejet = data.motif
    
    await db.commit()
    
    # TODO: Notifier le créateur du rejet
    # await notify_user_depense_rejected(db, depense)
    
    return {
        "message": "Dépense rejetée",
        "reference": depense.reference,
        "motif": data.motif
    }


# =============================================================================
# SUPPRIMER UNE DÉPENSE (Admin seulement)
# =============================================================================

@router.delete("/{id}")
async def delete_depense(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Supprimer une dépense
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut supprimer
    ⚠️ Les dépenses approuvées ne peuvent pas être supprimées
    """
    
    result = await db.execute(select(Depense).where(Depense.id == id))
    depense = result.scalar_one_or_none()
    
    if not depense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Dépense non trouvée"
        )
    
    # Empêcher la suppression des dépenses approuvées
    if depense.status == DepenseStatus.APPROUVEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une dépense approuvée. Utilisez une annulation."
        )
    
    # TODO: Logger pour audit AVANT suppression
    # await log_audit(db, user, "delete_depense", depense.id, {"reference": depense.reference})
    
    await db.delete(depense)
    await db.commit()
    
    return {"message": f"Dépense {depense.reference} supprimée"}


# =============================================================================
# STATISTIQUES DES DÉPENSES
# =============================================================================

@router.get("/stats/global")
async def get_depenses_stats(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_depenses"))
):
    """
    Statistiques des dépenses
    
    - Total des dépenses
    - Nombre par statut
    - Par catégorie
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Vérifier accès aux stats globales
    if chantier_id:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Construire la query
    query = select(Depense)
    if chantier_id:
        query = query.where(Depense.chantier_id == chantier_id)
    
    # Si pas admin/comptable/direction, filtrer par chantiers assignés
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
        chantiers_assignes = user.get("chantiers_assignes", [])
        user_chantier_id = user.get("chantier_id")
        if user_chantier_id:
            chantiers_assignes.append(user_chantier_id)
        if chantiers_assignes:
            query = query.where(Depense.chantier_id.in_(chantiers_assignes))
    
    result = await db.execute(query)
    depenses = result.scalars().all()
    
    # Calculer les stats
    total = sum(d.montant for d in depenses)
    en_attente = len([d for d in depenses if d.status == DepenseStatus.EN_ATTENTE])
    approuvees = len([d for d in depenses if d.status == DepenseStatus.APPROUVEE])
    rejetees = len([d for d in depenses if d.status == DepenseStatus.REJETEE])
    
    # Stats par catégorie
    categories = {}
    for d in depenses:
        cat = d.categorie or "Autre"
        if cat not in categories:
            categories[cat] = {"count": 0, "total": 0}
        categories[cat]["count"] += 1
        categories[cat]["total"] += d.montant
    
    return {
        "total_montant": total,
        "nb_depenses": len(depenses),
        "en_attente": en_attente,
        "approuvees": approuvees,
        "rejetees": rejetees,
        "total_approuve": sum(d.montant for d in depenses if d.status == DepenseStatus.APPROUVEE),
        "par_categorie": categories
    }


# =============================================================================
# DÉPENSES EN ATTENTE D'APPROBATION
# =============================================================================

@router.get("/pending/list")
async def list_pending_depenses(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())
):
    """
    Liste des dépenses en attente d'approbation
    
    ⚠️ Réservé à l'Administrateur Général
    """
    
    query = select(Depense).where(
        Depense.status.in_([DepenseStatus.EN_ATTENTE, DepenseStatus.VALIDEE_CHANTIER])
    ).order_by(Depense.created_at.asc())
    
    result = await db.execute(query)
    depenses = result.scalars().all()
    
    return {
        "count": len(depenses),
        "depenses": depenses
    }


# =============================================================================
# EXPORT DES DÉPENSES
# =============================================================================

@router.get("/export")
async def export_depenses(
    chantier_id: Optional[int] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("export_finances"))
):
    """
    Exporter les dépenses
    
    Accès: Admin Général, Comptable
    """
    
    query = select(Depense)
    
    if chantier_id:
        query = query.where(Depense.chantier_id == chantier_id)
    if date_debut:
        query = query.where(Depense.date_depense >= date_debut)
    if date_fin:
        query = query.where(Depense.date_depense <= date_fin)
    
    query = query.order_by(Depense.date_depense.desc())
    result = await db.execute(query)
    depenses = result.scalars().all()
    
    # TODO: Implémenter l'export CSV si nécessaire
    # if format == "csv":
    #     return generate_csv(depenses)
    
    return {
        "count": len(depenses),
        "depenses": depenses,
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": user.get("email")
    }