"""
NEXUS GROUP - Notifications Endpoints
======================================
Gestion des notifications avec contrôle d'accès par rôle

Permissions:
- Tous les utilisateurs: Voir leurs propres notifications
- Admin Général: Gérer les notifications + envoyer à tous
- Magasinier: Alertes stock automatiques
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum
from app.core.permissions import (
    require_permission,
    require_admin,
    has_permission
)
from app.models.notification import Notification
from app.models.materiel import Materiel
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =============================================================================
# SCHÉMAS
# =============================================================================

class NotificationCreate(BaseModel):
    titre: str
    message: str
    type_notif: str = "info"  # info, warning, error, success
    categorie: str = "general"  # general, stock, depense, tache, chantier
    user_id: Optional[int] = None  # Si None, pour tous
    chantier_id: Optional[int] = None


class NotificationBroadcast(BaseModel):
    titre: str
    message: str
    type_notif: str = "info"
    categorie: str = "general"
    roles: Optional[List[str]] = None  # Si None, tous les utilisateurs
    chantier_id: Optional[int] = None


# =============================================================================
# TYPES DE NOTIFICATIONS
# =============================================================================

class NotificationType:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationCategorie:
    GENERAL = "general"
    STOCK = "stock"
    DEPENSE = "depense"
    TACHE = "tache"
    CHANTIER = "chantier"
    DOCUMENT = "document"
    VALIDATION = "validation"


# =============================================================================
# LISTE DES NOTIFICATIONS
# =============================================================================

@router.get("/", response_model=List[dict])
async def list_notifications(
    non_lues: bool = Query(False, description="Seulement les non lues"),
    categorie: Optional[str] = Query(None, description="Filtrer par catégorie"),
    limit: int = Query(50, le=100, description="Nombre max de résultats"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Liste des notifications de l'utilisateur connecté
    
    Chaque utilisateur ne voit que SES notifications
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    query = select(Notification).where(Notification.user_id == user_id)
    
    if non_lues:
        query = query.where(Notification.is_read == False)
    
    if categorie:
        query = query.where(Notification.categorie == categorie)
    
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [{
        "id": n.id,
        "titre": n.titre,
        "message": n.message,
        "type_notif": n.type_notif,
        "categorie": n.categorie,
        "is_read": n.is_read,
        "chantier_id": n.chantier_id,
        "created_at": n.created_at.isoformat() if n.created_at else None
    } for n in notifications]


# =============================================================================
# COMPTER LES NOTIFICATIONS NON LUES
# =============================================================================

@router.get("/count")
async def count_non_lues(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Nombre de notifications non lues
    
    Utile pour afficher un badge dans l'interface
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    
    return {"count": count}


# =============================================================================
# MARQUER UNE NOTIFICATION COMME LUE
# =============================================================================

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Marquer une notification comme lue
    
    L'utilisateur ne peut marquer que SES notifications
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notif = result.scalar_one_or_none()
    
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification non trouvée"
        )
    
    # Vérifier que c'est bien sa notification
    if notif.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas modifier cette notification"
        )
    
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Notification marquée comme lue"}


# =============================================================================
# MARQUER TOUTES COMME LUES
# =============================================================================

@router.put("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Marquer toutes les notifications comme lues
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    
    return {"message": "Toutes les notifications marquées comme lues"}


# =============================================================================
# SUPPRIMER UNE NOTIFICATION
# =============================================================================

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Supprimer une notification
    
    L'utilisateur ne peut supprimer que SES notifications
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notif = result.scalar_one_or_none()
    
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Notification non trouvée"
        )
    
    # Vérifier que c'est bien sa notification
    if notif.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez pas supprimer cette notification"
        )
    
    await db.delete(notif)
    await db.commit()
    
    return {"message": "Notification supprimée"}


# =============================================================================
# SUPPRIMER TOUTES LES NOTIFICATIONS LUES
# =============================================================================

@router.delete("/clear-read")
async def clear_read_notifications(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Supprimer toutes les notifications lues
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == True
        )
    )
    notifications = result.scalars().all()
    
    count = len(notifications)
    for notif in notifications:
        await db.delete(notif)
    
    await db.commit()
    
    return {"message": f"{count} notification(s) supprimée(s)"}


# =============================================================================
# VÉRIFIER LES ALERTES DE STOCK (Admin/Magasinier)
# =============================================================================

@router.post("/check-stock/")
async def check_stock_alerts(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_stock"))
):
    """
    Vérifier les alertes de stock et créer des notifications
    
    - Crée des notifications pour les matériels sous le seuil d'alerte
    - Envoie aux admins et magasiniers
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Récupérer les matériels en alerte
    result = await db.execute(
        select(Materiel).where(Materiel.quantite <= Materiel.seuil_alerte)
    )
    materiels_bas = result.scalars().all()
    
    # Récupérer les utilisateurs à notifier (Admin et Magasinier)
    result_users = await db.execute(
        select(User).where(
            User.role.in_([RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER]),
            User.is_active == True
        )
    )
    users_to_notify = result_users.scalars().all()
    
    created = 0
    for m in materiels_bas:
        for u in users_to_notify:
            # Vérifier si notification existe déjà (non lue)
            existing = await db.execute(
                select(Notification).where(
                    Notification.user_id == u.id,
                    Notification.categorie == NotificationCategorie.STOCK,
                    Notification.message.contains(m.nom),
                    Notification.is_read == False
                )
            )
            if not existing.scalar_one_or_none():
                notif = Notification(
                    titre="⚠️ Stock Bas",
                    message=f"{m.nom}: {m.quantite} {m.unite} restant(s) (seuil: {m.seuil_alerte})",
                    type_notif=NotificationType.WARNING,
                    categorie=NotificationCategorie.STOCK,
                    user_id=u.id,
                    chantier_id=m.chantier_id
                )
                db.add(notif)
                created += 1
    
    await db.commit()
    
    return {
        "message": f"{created} alerte(s) créée(s)",
        "materiels_en_alerte": len(materiels_bas),
        "utilisateurs_notifies": len(users_to_notify)
    }


# =============================================================================
# CRÉER UNE NOTIFICATION (Admin)
# =============================================================================

@router.post("/")
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Créer une notification pour un utilisateur spécifique
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut créer des notifications
    """
    
    if not data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id est requis. Utilisez /broadcast pour envoyer à plusieurs utilisateurs."
        )
    
    # Vérifier que l'utilisateur existe
    result = await db.execute(select(User).where(User.id == data.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    notif = Notification(
        titre=data.titre,
        message=data.message,
        type_notif=data.type_notif,
        categorie=data.categorie,
        user_id=data.user_id,
        chantier_id=data.chantier_id
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    
    return {
        "message": "Notification créée",
        "notification_id": notif.id
    }


# =============================================================================
# DIFFUSER UNE NOTIFICATION (Admin)
# =============================================================================

@router.post("/broadcast")
async def broadcast_notification(
    data: NotificationBroadcast,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Envoyer une notification à plusieurs utilisateurs
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut diffuser des notifications
    
    Options:
    - roles: Liste des rôles à notifier (si None, tous les utilisateurs)
    - chantier_id: Si spécifié, seulement les utilisateurs de ce chantier
    """
    
    query = select(User).where(User.is_active == True)
    
    # Filtrer par rôles si spécifié
    if data.roles:
        query = query.where(User.role.in_(data.roles))
    
    # Filtrer par chantier si spécifié
    if data.chantier_id:
        query = query.where(User.chantier_id == data.chantier_id)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    created = 0
    for u in users:
        notif = Notification(
            titre=data.titre,
            message=data.message,
            type_notif=data.type_notif,
            categorie=data.categorie,
            user_id=u.id,
            chantier_id=data.chantier_id
        )
        db.add(notif)
        created += 1
    
    await db.commit()
    
    return {
        "message": f"Notification envoyée à {created} utilisateur(s)",
        "roles_cibles": data.roles or "tous",
        "chantier_id": data.chantier_id
    }


# =============================================================================
# NOTIFICATIONS PAR CATÉGORIE (Stats)
# =============================================================================

@router.get("/stats")
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_notifications"))
):
    """
    Statistiques des notifications de l'utilisateur
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    result = await db.execute(
        select(Notification).where(Notification.user_id == user_id)
    )
    notifications = result.scalars().all()
    
    # Par catégorie
    par_categorie = {}
    non_lues = 0
    for n in notifications:
        cat = n.categorie or "general"
        if cat not in par_categorie:
            par_categorie[cat] = {"total": 0, "non_lues": 0}
        par_categorie[cat]["total"] += 1
        if not n.is_read:
            par_categorie[cat]["non_lues"] += 1
            non_lues += 1
    
    return {
        "total": len(notifications),
        "non_lues": non_lues,
        "par_categorie": par_categorie
    }


# =============================================================================
# HELPER: CRÉER UNE NOTIFICATION SYSTÈME
# =============================================================================

async def create_system_notification(
    db: AsyncSession,
    user_id: int,
    titre: str,
    message: str,
    type_notif: str = NotificationType.INFO,
    categorie: str = NotificationCategorie.GENERAL,
    chantier_id: int = None
):
    """
    Fonction helper pour créer des notifications depuis d'autres modules
    
    Usage:
        await create_system_notification(
            db=db,
            user_id=user.id,
            titre="Dépense approuvée",
            message="Votre dépense DEP-2024-001 a été approuvée",
            type_notif="success",
            categorie="depense"
        )
    """
    notif = Notification(
        titre=titre,
        message=message,
        type_notif=type_notif,
        categorie=categorie,
        user_id=user_id,
        chantier_id=chantier_id
    )
    db.add(notif)
    await db.commit()
    return notif


async def notify_admins(
    db: AsyncSession,
    titre: str,
    message: str,
    type_notif: str = NotificationType.INFO,
    categorie: str = NotificationCategorie.GENERAL,
    chantier_id: int = None
):
    """
    Envoyer une notification à tous les admins
    """
    result = await db.execute(
        select(User).where(
            User.role == RoleEnum.ADMIN_GENERAL,
            User.is_active == True
        )
    )
    admins = result.scalars().all()
    
    for admin in admins:
        notif = Notification(
            titre=titre,
            message=message,
            type_notif=type_notif,
            categorie=categorie,
            user_id=admin.id,
            chantier_id=chantier_id
        )
        db.add(notif)
    
    await db.commit()