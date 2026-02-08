"""
NEXUS GROUP - Matériels & Stock Endpoints
==========================================
Gestion du stock et des mouvements avec contrôle d'accès par rôle

Permissions:
- Admin Général: CRUD total + transferts inter-chantiers
- Magasinier: Gestion complète du stock (entrées/sorties/transferts)
- Admin Chantier: Voir stock de ses chantiers
- Chef Chantier: Voir stock de son chantier + demandes
- Direction: Lecture seule tous les stocks
- Comptable: ❌ Pas d'accès au stock
- Ouvrier: ❌ Pas d'accès
- Client: ❌ Pas d'accès
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_admin,
    require_roles,
    has_permission
)
from app.models.materiel import Materiel, MouvementStock
from app.models.chantier import Chantier
from app.schemas.materiel import MaterielCreate, MaterielResponse, MouvementCreate, MouvementResponse

router = APIRouter(prefix="/materiels", tags=["Materiels"])


# =============================================================================
# SCHÉMAS ADDITIONNELS
# =============================================================================

class MaterielUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    unite: Optional[str] = None
    quantite: Optional[float] = None
    seuil_alerte: Optional[float] = None
    prix_unitaire: Optional[float] = None
    chantier_id: Optional[int] = None
    categorie: Optional[str] = None


class TransfertRequest(BaseModel):
    materiel_id: int
    quantite: float
    chantier_source_id: int
    chantier_destination_id: int
    motif: Optional[str] = None


class ReceptionRequest(BaseModel):
    materiel_id: int
    quantite: float
    fournisseur: Optional[str] = None
    bon_livraison: Optional[str] = None
    motif: Optional[str] = None


# =============================================================================
# TYPES DE MOUVEMENTS
# =============================================================================

class TypeMouvement:
    ENTREE = "entree"
    SORTIE = "sortie"
    TRANSFERT_ENTRANT = "transfert_entrant"
    TRANSFERT_SORTANT = "transfert_sortant"
    AJUSTEMENT = "ajustement"
    RECEPTION = "reception"


# =============================================================================
# LISTE DES MATÉRIELS
# =============================================================================

@router.get("/", response_model=List[MaterielResponse])
async def list_materiels(
    chantier_id: Optional[int] = Query(None, description="Filtrer par chantier"),
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie"),
    en_alerte: Optional[bool] = Query(None, description="Seulement les alertes"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Liste des matériels selon le rôle:
    
    - Admin Général, Magasinier, Direction: Tout le stock
    - Admin Chantier, Chef Chantier: Stock de leurs chantiers
    - Comptable, Ouvrier, Client: ❌ Pas d'accès
    """
    role = user.get("role", RoleEnum.OUVRIER)
    chantiers_assignes = user.get("chantiers_assignes", [])
    user_chantier_id = user.get("chantier_id")
    
    query = select(Materiel)
    
    # Filtrage par rôle
    if role in [RoleEnum.ADMIN_CHANTIER, RoleEnum.CHEF_CHANTIER]:
        # Seulement leurs chantiers
        if chantiers_assignes:
            query = query.where(Materiel.chantier_id.in_(chantiers_assignes))
        elif user_chantier_id:
            query = query.where(Materiel.chantier_id == user_chantier_id)
    
    # Filtres additionnels
    if chantier_id:
        # Vérifier l'accès
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès au stock de ce chantier"
                )
        query = query.where(Materiel.chantier_id == chantier_id)
    
    if categorie:
        query = query.where(Materiel.categorie == categorie)
    
    if en_alerte:
        query = query.where(Materiel.quantite <= Materiel.seuil_alerte)
    
    query = query.order_by(Materiel.nom)
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# CRÉER UN MATÉRIEL
# =============================================================================

@router.post("/", response_model=MaterielResponse)
async def create_materiel(
    data: MaterielCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("create_stock"))
):
    """
    Ajouter un nouveau matériel au stock
    
    Permissions:
    - Admin Général: Tous les chantiers
    - Magasinier: Tous les chantiers
    - Chef Chantier: Son chantier seulement
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Chef Chantier: vérifier que c'est son chantier
    if role == RoleEnum.CHEF_CHANTIER:
        if data.chantier_id and not has_chantier_access(user, data.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez ajouter du matériel qu'à votre chantier"
            )
    
    # Vérifier que le chantier existe
    if data.chantier_id:
        result = await db.execute(select(Chantier).where(Chantier.id == data.chantier_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chantier non trouvé"
            )
    
    materiel = Materiel(
        **data.model_dump(),
        created_by=user_id
    )
    db.add(materiel)
    await db.commit()
    await db.refresh(materiel)
    
    # Créer un mouvement d'entrée initial si quantité > 0
    if materiel.quantite and materiel.quantite > 0:
        mouvement = MouvementStock(
            materiel_id=materiel.id,
            type_mouvement=TypeMouvement.ENTREE,
            quantite=materiel.quantite,
            motif="Stock initial",
            created_by=user_id
        )
        db.add(mouvement)
        await db.commit()
    
    return materiel


# =============================================================================
# DÉTAIL D'UN MATÉRIEL
# =============================================================================

@router.get("/{id}", response_model=MaterielResponse)
async def get_materiel(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Récupérer les détails d'un matériel
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Materiel).where(Materiel.id == id))
    materiel = result.scalar_one_or_none()
    
    if not materiel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Matériel non trouvé"
        )
    
    # Vérifier l'accès au chantier
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER, RoleEnum.DIRECTION]:
        if materiel.chantier_id and not has_chantier_access(user, materiel.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce matériel"
            )
    
    return materiel


# =============================================================================
# MODIFIER UN MATÉRIEL
# =============================================================================

@router.put("/{id}", response_model=MaterielResponse)
async def update_materiel(
    id: int,
    data: MaterielUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("edit_stock"))
):
    """
    Modifier un matériel
    
    Permissions:
    - Admin Général, Magasinier: Tous les matériels
    - Chef Chantier: Matériels de son chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(select(Materiel).where(Materiel.id == id))
    materiel = result.scalar_one_or_none()
    
    if not materiel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Matériel non trouvé"
        )
    
    # Vérifier l'accès
    if role == RoleEnum.CHEF_CHANTIER:
        if not has_chantier_access(user, materiel.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce matériel"
            )
    
    # Si modification de quantité directe, créer un mouvement d'ajustement
    if data.quantite is not None and data.quantite != materiel.quantite:
        difference = data.quantite - materiel.quantite
        mouvement = MouvementStock(
            materiel_id=materiel.id,
            type_mouvement=TypeMouvement.AJUSTEMENT,
            quantite=abs(difference),
            motif=f"Ajustement manuel: {'augmentation' if difference > 0 else 'diminution'}",
            created_by=user_id
        )
        db.add(mouvement)
    
    # Mettre à jour
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(materiel, field, value)
    
    materiel.updated_at = datetime.utcnow()
    materiel.updated_by = user_id
    
    await db.commit()
    await db.refresh(materiel)
    
    return materiel


# =============================================================================
# SUPPRIMER UN MATÉRIEL
# =============================================================================

@router.delete("/{id}")
async def delete_materiel(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Supprimer un matériel
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut supprimer
    """
    
    result = await db.execute(select(Materiel).where(Materiel.id == id))
    materiel = result.scalar_one_or_none()
    
    if not materiel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Matériel non trouvé"
        )
    
    # Vérifier qu'il n'y a pas de stock
    if materiel.quantite and materiel.quantite > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer: stock restant de {materiel.quantite} {materiel.unite}"
        )
    
    await db.delete(materiel)
    await db.commit()
    
    return {"message": f"Matériel '{materiel.nom}' supprimé"}


# =============================================================================
# ALERTES DE STOCK
# =============================================================================

@router.get("/alertes/", response_model=List[MaterielResponse])
async def get_alertes_stock(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Liste des matériels en alerte (quantité <= seuil)
    
    Utile pour le magasinier et les chefs de chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(Materiel).where(Materiel.quantite <= Materiel.seuil_alerte)
    
    # Filtrer par chantier si demandé
    if chantier_id:
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce chantier"
                )
        query = query.where(Materiel.chantier_id == chantier_id)
    
    # Filtrer par chantiers accessibles
    if role in [RoleEnum.ADMIN_CHANTIER, RoleEnum.CHEF_CHANTIER]:
        chantiers_assignes = user.get("chantiers_assignes", [])
        user_chantier_id = user.get("chantier_id")
        if chantiers_assignes:
            query = query.where(Materiel.chantier_id.in_(chantiers_assignes))
        elif user_chantier_id:
            query = query.where(Materiel.chantier_id == user_chantier_id)
    
    query = query.order_by(Materiel.quantite)
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# CRÉER UN MOUVEMENT DE STOCK
# =============================================================================

@router.post("/mouvements/", response_model=MouvementResponse)
async def create_mouvement(
    data: MouvementCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("mouvement_stock"))
):
    """
    Enregistrer un mouvement de stock (entrée/sortie)
    
    Permissions:
    - Admin Général, Magasinier: Tous les matériels
    - Chef Chantier: Matériels de son chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Récupérer le matériel
    result = await db.execute(select(Materiel).where(Materiel.id == data.materiel_id))
    materiel = result.scalar_one_or_none()
    
    if not materiel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Matériel non trouvé"
        )
    
    # Vérifier l'accès au chantier
    if role == RoleEnum.CHEF_CHANTIER:
        if not has_chantier_access(user, materiel.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce matériel"
            )
    
    # Valider le type de mouvement
    if data.type_mouvement not in [TypeMouvement.ENTREE, TypeMouvement.SORTIE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type de mouvement invalide. Utilisez 'entree' ou 'sortie'"
        )
    
    # Mettre à jour la quantité
    if data.type_mouvement == TypeMouvement.ENTREE:
        materiel.quantite = (materiel.quantite or 0) + data.quantite
    elif data.type_mouvement == TypeMouvement.SORTIE:
        if (materiel.quantite or 0) < data.quantite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Stock insuffisant. Disponible: {materiel.quantite} {materiel.unite}"
            )
        materiel.quantite -= data.quantite
    
    # Créer le mouvement
    mouvement = MouvementStock(
        materiel_id=data.materiel_id,
        type_mouvement=data.type_mouvement,
        quantite=data.quantite,
        motif=data.motif,
        created_by=user_id
    )
    db.add(mouvement)
    
    materiel.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(mouvement)
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "mouvement_stock", mouvement.id)
    
    return mouvement


# =============================================================================
# RÉCEPTION DE MATÉRIAUX
# =============================================================================

@router.post("/reception/")
async def recevoir_materiel(
    data: ReceptionRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("receive_materiel"))
):
    """
    Enregistrer une réception de matériaux (livraison fournisseur)
    
    ⚠️ Réservé au Magasinier et Admin
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Récupérer le matériel
    result = await db.execute(select(Materiel).where(Materiel.id == data.materiel_id))
    materiel = result.scalar_one_or_none()
    
    if not materiel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matériel non trouvé"
        )
    
    # Augmenter le stock
    materiel.quantite = (materiel.quantite or 0) + data.quantite
    materiel.updated_at = datetime.utcnow()
    
    # Créer le mouvement
    motif = f"Réception: {data.motif or ''}"
    if data.fournisseur:
        motif += f" | Fournisseur: {data.fournisseur}"
    if data.bon_livraison:
        motif += f" | BL: {data.bon_livraison}"
    
    mouvement = MouvementStock(
        materiel_id=data.materiel_id,
        type_mouvement=TypeMouvement.RECEPTION,
        quantite=data.quantite,
        motif=motif,
        created_by=user_id
    )
    db.add(mouvement)
    
    await db.commit()
    await db.refresh(mouvement)
    
    return {
        "message": f"Réception enregistrée: +{data.quantite} {materiel.unite} de {materiel.nom}",
        "nouveau_stock": materiel.quantite,
        "mouvement_id": mouvement.id
    }


# =============================================================================
# TRANSFERT INTER-CHANTIERS
# =============================================================================

@router.post("/transfert/")
async def transferer_materiel(
    data: TransfertRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("transfer_stock"))
):
    """
    Transférer du matériel d'un chantier à un autre
    
    ⚠️ Réservé au Magasinier et Admin
    
    Crée 2 mouvements:
    - Sortie du chantier source
    - Entrée dans le chantier destination
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Vérifier les chantiers
    result_source = await db.execute(select(Chantier).where(Chantier.id == data.chantier_source_id))
    if not result_source.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chantier source non trouvé")
    
    result_dest = await db.execute(select(Chantier).where(Chantier.id == data.chantier_destination_id))
    if not result_dest.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chantier destination non trouvé")
    
    # Récupérer le matériel source
    result = await db.execute(
        select(Materiel).where(
            Materiel.id == data.materiel_id,
            Materiel.chantier_id == data.chantier_source_id
        )
    )
    materiel_source = result.scalar_one_or_none()
    
    if not materiel_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matériel non trouvé dans le chantier source"
        )
    
    # Vérifier le stock
    if (materiel_source.quantite or 0) < data.quantite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuffisant. Disponible: {materiel_source.quantite} {materiel_source.unite}"
        )
    
    # Diminuer le stock source
    materiel_source.quantite -= data.quantite
    
    # Chercher ou créer le matériel dans le chantier destination
    result_dest_mat = await db.execute(
        select(Materiel).where(
            Materiel.nom == materiel_source.nom,
            Materiel.chantier_id == data.chantier_destination_id
        )
    )
    materiel_dest = result_dest_mat.scalar_one_or_none()
    
    if materiel_dest:
        # Augmenter le stock existant
        materiel_dest.quantite = (materiel_dest.quantite or 0) + data.quantite
    else:
        # Créer le matériel dans le chantier destination
        materiel_dest = Materiel(
            nom=materiel_source.nom,
            description=materiel_source.description,
            unite=materiel_source.unite,
            quantite=data.quantite,
            seuil_alerte=materiel_source.seuil_alerte,
            prix_unitaire=materiel_source.prix_unitaire,
            categorie=materiel_source.categorie,
            chantier_id=data.chantier_destination_id,
            created_by=user_id
        )
        db.add(materiel_dest)
    
    # Créer les mouvements
    motif = data.motif or f"Transfert vers chantier #{data.chantier_destination_id}"
    
    mouvement_sortie = MouvementStock(
        materiel_id=materiel_source.id,
        type_mouvement=TypeMouvement.TRANSFERT_SORTANT,
        quantite=data.quantite,
        motif=f"Transfert vers chantier #{data.chantier_destination_id}: {motif}",
        created_by=user_id
    )
    db.add(mouvement_sortie)
    
    await db.commit()
    await db.refresh(materiel_dest)
    
    mouvement_entree = MouvementStock(
        materiel_id=materiel_dest.id,
        type_mouvement=TypeMouvement.TRANSFERT_ENTRANT,
        quantite=data.quantite,
        motif=f"Transfert depuis chantier #{data.chantier_source_id}: {motif}",
        created_by=user_id
    )
    db.add(mouvement_entree)
    
    await db.commit()
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "transfer_stock", {"source": data.chantier_source_id, "dest": data.chantier_destination_id})
    
    return {
        "message": f"Transfert effectué: {data.quantite} {materiel_source.unite} de {materiel_source.nom}",
        "chantier_source": {
            "id": data.chantier_source_id,
            "nouveau_stock": materiel_source.quantite
        },
        "chantier_destination": {
            "id": data.chantier_destination_id,
            "nouveau_stock": materiel_dest.quantite
        }
    }


# =============================================================================
# HISTORIQUE DES MOUVEMENTS
# =============================================================================

@router.get("/mouvements/", response_model=List[MouvementResponse])
async def list_mouvements(
    materiel_id: Optional[int] = None,
    chantier_id: Optional[int] = None,
    type_mouvement: Optional[str] = None,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_historique_stock"))
):
    """
    Historique des mouvements de stock
    
    Permissions:
    - Admin, Magasinier, Direction: Tous les mouvements
    - Autres: Selon accès chantier
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(MouvementStock)
    
    if materiel_id:
        query = query.where(MouvementStock.materiel_id == materiel_id)
    
    if type_mouvement:
        query = query.where(MouvementStock.type_mouvement == type_mouvement)
    
    if date_debut:
        date_debut_obj = datetime.strptime(date_debut, "%Y-%m-%d")
        query = query.where(MouvementStock.created_at >= date_debut_obj)
    
    if date_fin:
        date_fin_obj = datetime.strptime(date_fin, "%Y-%m-%d")
        query = query.where(MouvementStock.created_at <= date_fin_obj)
    
    # TODO: Filtrer par chantier si nécessaire
    # if chantier_id:
    #     query = query.join(Materiel).where(Materiel.chantier_id == chantier_id)
    
    query = query.order_by(MouvementStock.created_at.desc()).limit(100)
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# STATISTIQUES DU STOCK
# =============================================================================

@router.get("/stats/")
async def get_stock_stats(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Statistiques du stock
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(Materiel)
    
    if chantier_id:
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce chantier"
                )
        query = query.where(Materiel.chantier_id == chantier_id)
    
    result = await db.execute(query)
    materiels = result.scalars().all()
    
    # Calculer les stats
    total_articles = len(materiels)
    en_alerte = len([m for m in materiels if (m.quantite or 0) <= (m.seuil_alerte or 0)])
    rupture = len([m for m in materiels if (m.quantite or 0) == 0])
    
    # Valeur du stock (si prix_unitaire disponible)
    valeur_stock = sum(
        (m.quantite or 0) * (m.prix_unitaire or 0) 
        for m in materiels
    )
    
    # Par catégorie
    par_categorie = {}
    for m in materiels:
        cat = m.categorie or "Non catégorisé"
        if cat not in par_categorie:
            par_categorie[cat] = {"count": 0, "en_alerte": 0}
        par_categorie[cat]["count"] += 1
        if (m.quantite or 0) <= (m.seuil_alerte or 0):
            par_categorie[cat]["en_alerte"] += 1
    
    return {
        "total_articles": total_articles,
        "en_alerte": en_alerte,
        "en_rupture": rupture,
        "valeur_stock": valeur_stock,
        "par_categorie": par_categorie
    }


# =============================================================================
# CATÉGORIES DE MATÉRIELS
# =============================================================================

@router.get("/categories/")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Liste des catégories de matériels
    """
    result = await db.execute(
        select(Materiel.categorie).distinct().where(Materiel.categorie != None)
    )
    categories = [row[0] for row in result.all()]
    
    return {"categories": sorted(categories)}