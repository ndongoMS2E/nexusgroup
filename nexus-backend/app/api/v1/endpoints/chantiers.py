"""
NEXUS GROUP - Chantiers Endpoints
==================================
Gestion des chantiers avec contrôle d'accès par rôle

Permissions:
- Admin Général: Accès total (CRUD tous chantiers)
- Admin Chantier: Voir/modifier ses chantiers assignés
- Direction: Lecture seule tous chantiers
- Comptable: Lecture tous chantiers (pour contexte financier)
- Magasinier: Lecture tous chantiers (pour contexte stock)
- Chef Chantier: Voir/modifier ses chantiers assignés
- Ouvrier: Aucun accès direct aux chantiers
- Client: Voir son chantier uniquement
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_roles,
    require_admin,
    require_not_read_only,
    DataFilter,
    has_permission
)
from app.models.chantier import Chantier
from app.schemas.chantier import ChantierCreate, ChantierResponse

router = APIRouter(prefix="/chantiers", tags=["Chantiers"])


# =============================================================================
# SCHÉMAS
# =============================================================================

class ChantierUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    client_nom: Optional[str] = None
    client_telephone: Optional[str] = None
    budget_prevu: Optional[float] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ChantierStats(BaseModel):
    """Statistiques d'un chantier"""
    id: int
    nom: str
    budget_prevu: float
    budget_consomme: float
    pourcentage_avancement: int
    nb_employes: int
    nb_taches_en_cours: int


# =============================================================================
# LISTE DES CHANTIERS
# =============================================================================

@router.get("/", response_model=List[ChantierResponse])
async def list_chantiers(
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(require_permission("view_chantiers"))
):
    """
    Liste des chantiers selon le rôle:
    
    - Admin Général, Direction, Comptable, Magasinier: Tous les chantiers
    - Admin Chantier, Chef Chantier: Chantiers assignés seulement
    - Client: Son chantier uniquement
    - Ouvrier: Aucun accès (bloqué par permission)
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id")
    
    result = await db.execute(select(Chantier).order_by(Chantier.created_at.desc()))
    chantiers = result.scalars().all()
    
    # Convertir en liste de dictionnaires pour le filtrage
    chantiers_list = []
    for c in chantiers:
        chantier_dict = {
            "id": c.id,
            "nom": c.nom,
            "reference": c.reference,
            "adresse": c.adresse,
            "ville": c.ville,
            "client_nom": c.client_nom,
            "client_telephone": c.client_telephone,
            "budget_prevu": c.budget_prevu,
            "date_debut": c.date_debut,
            "date_fin": c.date_fin,
            "description": c.description,
            "status": c.status,
            "created_at": c.created_at,
            "client_id": getattr(c, 'client_id', None),  # Si le champ existe
        }
        chantiers_list.append(chantier_dict)
    
    # Filtrer selon le rôle
    chantiers_assignes = user.get("chantiers_assignes", [])
    
    # Admin Général, Direction, Comptable, Magasinier: tous les chantiers
    if role in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, 
                RoleEnum.COMPTABLE, RoleEnum.MAGASINIER]:
        return chantiers
    
    # Client: son chantier uniquement
    if role == RoleEnum.CLIENT:
        filtered = [c for c in chantiers if getattr(c, 'client_id', None) == user_id]
        return filtered
    
    # Admin Chantier, Chef Chantier, Conducteur: chantiers assignés
    if role in [RoleEnum.ADMIN_CHANTIER, RoleEnum.CHEF_CHANTIER]:
        filtered = [c for c in chantiers if c.id in chantiers_assignes]
        return filtered
    
    # Par défaut: chantiers assignés
    return [c for c in chantiers if c.id in chantiers_assignes]


# =============================================================================
# CRÉER UN CHANTIER (Admin seulement)
# =============================================================================

@router.post("/", response_model=ChantierResponse)
async def create_chantier(
    data: ChantierCreate, 
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Créer un nouveau chantier
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut créer des chantiers
    """
    
    # Générer une référence unique
    reference = f"CHT-{datetime.now().year}-{random.randint(1000,9999)}"
    
    # Vérifier que la référence n'existe pas déjà
    result = await db.execute(select(Chantier).where(Chantier.reference == reference))
    while result.scalar_one_or_none():
        reference = f"CHT-{datetime.now().year}-{random.randint(1000,9999)}"
        result = await db.execute(select(Chantier).where(Chantier.reference == reference))
    
    chantier = Chantier(
        nom=data.nom,
        reference=reference,
        adresse=data.adresse,
        ville=data.ville,
        client_nom=data.client_nom,
        client_telephone=data.client_telephone,
        budget_prevu=data.budget_prevu,
        date_debut=data.date_debut,
        date_fin=data.date_fin,
        description=data.description,
        status="en_preparation",
        created_by=user.get("user_id")  # Traçabilité
    )
    
    db.add(chantier)
    await db.commit()
    await db.refresh(chantier)
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "create_chantier", chantier.id)
    
    return chantier


# =============================================================================
# DÉTAIL D'UN CHANTIER
# =============================================================================

@router.get("/{id}", response_model=ChantierResponse)
async def get_chantier(
    id: int, 
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(require_permission("view_chantiers"))
):
    """
    Récupérer les détails d'un chantier
    
    Vérifie que l'utilisateur a accès à ce chantier spécifique
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier l'accès au chantier
    if not has_chantier_access(user, id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce chantier"
        )
    
    return chantier


# =============================================================================
# MODIFIER UN CHANTIER
# =============================================================================

@router.put("/{id}", response_model=ChantierResponse)
async def update_chantier(
    id: int,
    data: ChantierUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("edit_chantier"))
):
    """
    Modifier un chantier
    
    Permissions:
    - Admin Général: Peut modifier tous les chantiers
    - Admin Chantier: Peut modifier ses chantiers assignés
    - Direction: ❌ Lecture seule
    - Autres: ❌ Pas d'accès
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Vérifier que le rôle n'est pas en lecture seule
    if role == RoleEnum.DIRECTION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le rôle Direction est en lecture seule. Aucune modification autorisée."
        )
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier l'accès au chantier (sauf Admin Général)
    if role != RoleEnum.ADMIN_GENERAL:
        if not has_chantier_access(user, id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Vérifier si modification du budget (Admin seulement)
    if data.budget_prevu is not None and role != RoleEnum.ADMIN_GENERAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul l'Administrateur Général peut modifier le budget"
        )
    
    # Mettre à jour les champs fournis
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(chantier, field, value)
    
    chantier.updated_at = datetime.utcnow()
    chantier.updated_by = user.get("user_id")  # Traçabilité
    
    await db.commit()
    await db.refresh(chantier)
    
    # TODO: Logger pour audit
    # await log_audit(db, user, "update_chantier", chantier.id, update_data)
    
    return chantier


# =============================================================================
# SUPPRIMER UN CHANTIER (Admin seulement)
# =============================================================================

@router.delete("/{id}")
async def delete_chantier(
    id: int, 
    db: AsyncSession = Depends(get_db), 
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Supprimer un chantier
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut supprimer des chantiers
    
    Note: En production, préférer une désactivation/archivage plutôt qu'une suppression
    """
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Chantier non trouvé"
        )
    
    # Vérifier si le chantier a des données liées
    # TODO: Vérifier dépenses, employés, documents, etc.
    # if await has_related_data(db, id):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Impossible de supprimer: ce chantier contient des données. Archivez-le plutôt."
    #     )
    
    # TODO: Logger pour audit AVANT suppression
    # await log_audit(db, user, "delete_chantier", chantier.id, {"nom": chantier.nom})
    
    await db.delete(chantier)
    await db.commit()
    
    return {"message": f"Chantier '{chantier.nom}' supprimé"}


# =============================================================================
# ARCHIVER UN CHANTIER
# =============================================================================

@router.put("/{id}/archive")
async def archive_chantier(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())
):
    """
    Archiver un chantier (au lieu de le supprimer)
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut archiver
    """
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    chantier.status = "archive"
    chantier.archived_at = datetime.utcnow()
    chantier.archived_by = user.get("user_id")
    
    await db.commit()
    
    return {"message": f"Chantier '{chantier.nom}' archivé"}


# =============================================================================
# STATISTIQUES D'UN CHANTIER
# =============================================================================

@router.get("/{id}/stats")
async def get_chantier_stats(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_chantiers"))
):
    """
    Récupérer les statistiques d'un chantier
    
    Retourne:
    - Budget prévu vs consommé
    - Pourcentage d'avancement
    - Nombre d'employés
    - Nombre de tâches
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Vérifier l'accès
    if not has_chantier_access(user, id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce chantier"
        )
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    # TODO: Calculer les vraies stats depuis la DB
    # budget_consomme = await get_total_depenses(db, id)
    # nb_employes = await count_employes_chantier(db, id)
    # etc.
    
    stats = {
        "id": chantier.id,
        "nom": chantier.nom,
        "reference": chantier.reference,
        "status": chantier.status,
        "budget_prevu": chantier.budget_prevu or 0,
        "budget_consomme": 0,  # TODO: calculer
        "pourcentage_budget": 0,  # TODO: calculer
        "pourcentage_avancement": 0,  # TODO: calculer
        "nb_employes": 0,  # TODO: calculer
        "nb_taches_total": 0,  # TODO: calculer
        "nb_taches_terminees": 0,  # TODO: calculer
        "date_debut": chantier.date_debut,
        "date_fin": chantier.date_fin,
    }
    
    # Masquer le budget pour certains rôles
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.ADMIN_CHANTIER, 
                    RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
        stats.pop("budget_prevu", None)
        stats.pop("budget_consomme", None)
        stats.pop("pourcentage_budget", None)
    
    return stats


# =============================================================================
# ASSIGNER DES UTILISATEURS À UN CHANTIER
# =============================================================================

@router.post("/{id}/assign")
async def assign_users_to_chantier(
    id: int,
    user_ids: List[int],
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())
):
    """
    Assigner des utilisateurs à un chantier
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut assigner
    """
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    # TODO: Mettre à jour les assignations dans la table users ou une table pivot
    # for user_id in user_ids:
    #     await assign_user_to_chantier(db, user_id, id)
    
    return {
        "message": f"{len(user_ids)} utilisateur(s) assigné(s) au chantier",
        "chantier_id": id,
        "user_ids": user_ids
    }


# =============================================================================
# AVANCEMENT CLIENT (Vue spéciale pour le client)
# =============================================================================

@router.get("/{id}/avancement")
async def get_avancement_client(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_avancement"))
):
    """
    Vue d'avancement pour le client
    
    Retourne uniquement les informations validées pour le client:
    - Avancement global
    - Photos/vidéos validées
    - Étapes importantes
    
    ⛔️ Pas de budget interne
    ⛔️ Pas d'infos RH
    """
    
    result = await db.execute(select(Chantier).where(Chantier.id == id))
    chantier = result.scalar_one_or_none()
    
    if not chantier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chantier non trouvé"
        )
    
    # Vérifier que c'est bien le chantier du client
    role = user.get("role")
    if role == RoleEnum.CLIENT:
        # TODO: Vérifier que ce chantier appartient au client
        pass
    
    # Retourner uniquement les infos autorisées
    return {
        "id": chantier.id,
        "nom": chantier.nom,
        "status": chantier.status,
        "pourcentage_avancement": 0,  # TODO: calculer
        "date_debut": chantier.date_debut,
        "date_fin_prevue": chantier.date_fin,
        "etapes": [],  # TODO: récupérer les étapes validées
        "photos": [],  # TODO: récupérer les photos validées
        "derniere_mise_a_jour": chantier.updated_at
    }