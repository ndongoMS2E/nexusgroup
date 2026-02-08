"""
NEXUS GROUP - Notification Service
====================================
Service réutilisable pour créer et envoyer des notifications
depuis n'importe quel module de l'application.

Usage:
    from app.services.notification_service import NotificationService
    
    # Dans une route
    await NotificationService.notify_user(db, user_id, "Titre", "Message")
    await NotificationService.notify_admins(db, "Nouvelle dépense", "...")
    await NotificationService.notify_by_role(db, ["comptable", "admin_general"], "...")
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.models.notification import Notification
from app.models.user import User
from app.core.security import RoleEnum


# =============================================================================
# TYPES DE NOTIFICATIONS
# =============================================================================

class NotificationType:
    """Types de notifications disponibles"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationCategorie:
    """Catégories de notifications"""
    GENERAL = "general"
    STOCK = "stock"
    DEPENSE = "depense"
    TACHE = "tache"
    CHANTIER = "chantier"
    DOCUMENT = "document"
    VALIDATION = "validation"
    EMPLOYE = "employe"
    PAIEMENT = "paiement"
    SYSTEME = "systeme"


# =============================================================================
# SERVICE DE NOTIFICATIONS
# =============================================================================

class NotificationService:
    """Service centralisé pour la gestion des notifications"""
    
    # =========================================================================
    # NOTIFICATIONS INDIVIDUELLES
    # =========================================================================
    
    @staticmethod
    async def notify_user(
        db: AsyncSession,
        user_id: int,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.GENERAL,
        chantier_id: int = None
    ) -> Notification:
        """
        Envoyer une notification à un utilisateur spécifique
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur destinataire
            titre: Titre de la notification
            message: Corps du message
            type_notif: Type (info, warning, error, success)
            categorie: Catégorie (stock, depense, tache, etc.)
            chantier_id: ID du chantier concerné (optionnel)
        
        Returns:
            Notification créée
        
        Example:
            await NotificationService.notify_user(
                db=db,
                user_id=123,
                titre="✅ Dépense approuvée",
                message="Votre dépense DEP-2024-001 a été approuvée",
                type_notif=NotificationType.SUCCESS,
                categorie=NotificationCategorie.DEPENSE
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
        await db.refresh(notif)
        return notif
    
    # =========================================================================
    # NOTIFICATIONS PAR RÔLE
    # =========================================================================
    
    @staticmethod
    async def notify_by_role(
        db: AsyncSession,
        roles: List[str],
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.GENERAL,
        chantier_id: int = None
    ) -> int:
        """
        Envoyer une notification à tous les utilisateurs ayant certains rôles
        
        Args:
            db: Session de base de données
            roles: Liste des rôles à notifier
            titre: Titre de la notification
            message: Corps du message
            type_notif: Type de notification
            categorie: Catégorie
            chantier_id: ID du chantier concerné (optionnel)
        
        Returns:
            Nombre de notifications créées
        
        Example:
            await NotificationService.notify_by_role(
                db=db,
                roles=["comptable", "admin_general"],
                titre="💰 Nouvelle dépense à approuver",
                message="Dépense DEP-2024-001 en attente",
                categorie=NotificationCategorie.VALIDATION
            )
        """
        result = await db.execute(
            select(User).where(
                User.role.in_(roles),
                User.is_active == True
            )
        )
        users = result.scalars().all()
        
        count = 0
        for user in users:
            notif = Notification(
                titre=titre,
                message=message,
                type_notif=type_notif,
                categorie=categorie,
                user_id=user.id,
                chantier_id=chantier_id
            )
            db.add(notif)
            count += 1
        
        await db.commit()
        return count
    
    # =========================================================================
    # NOTIFICATIONS ADMIN
    # =========================================================================
    
    @staticmethod
    async def notify_admins(
        db: AsyncSession,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.GENERAL,
        chantier_id: int = None
    ) -> int:
        """
        Envoyer une notification à tous les administrateurs généraux
        
        Example:
            await NotificationService.notify_admins(
                db=db,
                titre="⚠️ Demande de validation",
                message="Une dépense importante nécessite votre approbation",
                type_notif=NotificationType.WARNING,
                categorie=NotificationCategorie.VALIDATION
            )
        """
        return await NotificationService.notify_by_role(
            db=db,
            roles=[RoleEnum.ADMIN_GENERAL],
            titre=titre,
            message=message,
            type_notif=type_notif,
            categorie=categorie,
            chantier_id=chantier_id
        )
    
    @staticmethod
    async def notify_admin_and_comptable(
        db: AsyncSession,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.GENERAL,
        chantier_id: int = None
    ) -> int:
        """
        Envoyer une notification aux admins et comptables
        Utile pour les notifications financières
        """
        return await NotificationService.notify_by_role(
            db=db,
            roles=[RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE],
            titre=titre,
            message=message,
            type_notif=type_notif,
            categorie=categorie,
            chantier_id=chantier_id
        )
    
    # =========================================================================
    # NOTIFICATIONS CHANTIER
    # =========================================================================
    
    @staticmethod
    async def notify_chantier_users(
        db: AsyncSession,
        chantier_id: int,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.CHANTIER,
        exclude_roles: List[str] = None
    ) -> int:
        """
        Envoyer une notification à tous les utilisateurs d'un chantier
        
        Args:
            db: Session de base de données
            chantier_id: ID du chantier
            titre: Titre de la notification
            message: Corps du message
            type_notif: Type de notification
            categorie: Catégorie
            exclude_roles: Rôles à exclure (optionnel)
        
        Example:
            await NotificationService.notify_chantier_users(
                db=db,
                chantier_id=1,
                titre="📢 Réunion de chantier",
                message="Réunion demain à 8h sur le chantier",
                exclude_roles=["ouvrier"]  # Ne pas notifier les ouvriers
            )
        """
        query = select(User).where(
            User.chantier_id == chantier_id,
            User.is_active == True
        )
        
        if exclude_roles:
            query = query.where(User.role.notin_(exclude_roles))
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        count = 0
        for user in users:
            notif = Notification(
                titre=titre,
                message=message,
                type_notif=type_notif,
                categorie=categorie,
                user_id=user.id,
                chantier_id=chantier_id
            )
            db.add(notif)
            count += 1
        
        await db.commit()
        return count
    
    # =========================================================================
    # NOTIFICATIONS STOCK (Magasinier)
    # =========================================================================
    
    @staticmethod
    async def notify_stock_alert(
        db: AsyncSession,
        materiel_nom: str,
        quantite: float,
        seuil: float,
        unite: str,
        chantier_id: int = None
    ) -> int:
        """
        Envoyer une alerte de stock bas aux admins et magasiniers
        
        Example:
            await NotificationService.notify_stock_alert(
                db=db,
                materiel_nom="Ciment",
                quantite=5,
                seuil=10,
                unite="sacs",
                chantier_id=1
            )
        """
        return await NotificationService.notify_by_role(
            db=db,
            roles=[RoleEnum.ADMIN_GENERAL, RoleEnum.MAGASINIER],
            titre="⚠️ Stock Bas",
            message=f"{materiel_nom}: {quantite} {unite} restant(s) (seuil: {seuil})",
            type_notif=NotificationType.WARNING,
            categorie=NotificationCategorie.STOCK,
            chantier_id=chantier_id
        )
    
    # =========================================================================
    # NOTIFICATIONS DÉPENSES
    # =========================================================================
    
    @staticmethod
    async def notify_depense_created(
        db: AsyncSession,
        depense_reference: str,
        montant: float,
        createur_nom: str,
        chantier_id: int = None
    ) -> int:
        """
        Notifier les admins qu'une nouvelle dépense est en attente
        """
        return await NotificationService.notify_admins(
            db=db,
            titre="💰 Nouvelle dépense à approuver",
            message=f"Dépense {depense_reference} de {montant:,.0f} FCFA créée par {createur_nom}",
            type_notif=NotificationType.INFO,
            categorie=NotificationCategorie.VALIDATION,
            chantier_id=chantier_id
        )
    
    @staticmethod
    async def notify_depense_approved(
        db: AsyncSession,
        user_id: int,
        depense_reference: str,
        montant: float
    ) -> Notification:
        """
        Notifier le créateur que sa dépense a été approuvée
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=user_id,
            titre="✅ Dépense approuvée",
            message=f"Votre dépense {depense_reference} de {montant:,.0f} FCFA a été approuvée",
            type_notif=NotificationType.SUCCESS,
            categorie=NotificationCategorie.DEPENSE
        )
    
    @staticmethod
    async def notify_depense_rejected(
        db: AsyncSession,
        user_id: int,
        depense_reference: str,
        motif: str
    ) -> Notification:
        """
        Notifier le créateur que sa dépense a été rejetée
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=user_id,
            titre="❌ Dépense rejetée",
            message=f"Votre dépense {depense_reference} a été rejetée. Motif: {motif}",
            type_notif=NotificationType.ERROR,
            categorie=NotificationCategorie.DEPENSE
        )
    
    # =========================================================================
    # NOTIFICATIONS DOCUMENTS
    # =========================================================================
    
    @staticmethod
    async def notify_document_validated(
        db: AsyncSession,
        client_user_id: int,
        document_nom: str,
        chantier_id: int
    ) -> Notification:
        """
        Notifier le client qu'un nouveau document est disponible
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=client_user_id,
            titre="📄 Nouveau document disponible",
            message=f"Le document '{document_nom}' est maintenant disponible pour consultation",
            type_notif=NotificationType.INFO,
            categorie=NotificationCategorie.DOCUMENT,
            chantier_id=chantier_id
        )
    
    # =========================================================================
    # NOTIFICATIONS TÂCHES
    # =========================================================================
    
    @staticmethod
    async def notify_tache_assigned(
        db: AsyncSession,
        user_id: int,
        tache_titre: str,
        chantier_id: int
    ) -> Notification:
        """
        Notifier un utilisateur qu'une tâche lui a été assignée
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=user_id,
            titre="📋 Nouvelle tâche assignée",
            message=f"La tâche '{tache_titre}' vous a été assignée",
            type_notif=NotificationType.INFO,
            categorie=NotificationCategorie.TACHE,
            chantier_id=chantier_id
        )
    
    @staticmethod
    async def notify_tache_completed(
        db: AsyncSession,
        chef_user_id: int,
        tache_titre: str,
        executant_nom: str,
        chantier_id: int
    ) -> Notification:
        """
        Notifier le chef de chantier qu'une tâche a été terminée
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=chef_user_id,
            titre="✅ Tâche terminée",
            message=f"La tâche '{tache_titre}' a été terminée par {executant_nom}",
            type_notif=NotificationType.SUCCESS,
            categorie=NotificationCategorie.TACHE,
            chantier_id=chantier_id
        )
    
    # =========================================================================
    # NOTIFICATIONS PAIEMENTS
    # =========================================================================
    
    @staticmethod
    async def notify_paiement_effectue(
        db: AsyncSession,
        employe_user_id: int,
        montant: float,
        periode: str
    ) -> Notification:
        """
        Notifier un employé que son paiement a été effectué
        """
        return await NotificationService.notify_user(
            db=db,
            user_id=employe_user_id,
            titre="💵 Paiement effectué",
            message=f"Votre salaire de {montant:,.0f} FCFA pour {periode} a été traité",
            type_notif=NotificationType.SUCCESS,
            categorie=NotificationCategorie.PAIEMENT
        )
    
    # =========================================================================
    # NOTIFICATIONS SYSTÈME
    # =========================================================================
    
    @staticmethod
    async def notify_all_users(
        db: AsyncSession,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO
    ) -> int:
        """
        Envoyer une notification à TOUS les utilisateurs actifs
        À utiliser avec précaution (maintenances, annonces importantes)
        """
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
        
        count = 0
        for user in users:
            notif = Notification(
                titre=titre,
                message=message,
                type_notif=type_notif,
                categorie=NotificationCategorie.SYSTEME,
                user_id=user.id
            )
            db.add(notif)
            count += 1
        
        await db.commit()
        return count
    
    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    
    @staticmethod
    async def check_duplicate(
        db: AsyncSession,
        user_id: int,
        categorie: str,
        message_contains: str
    ) -> bool:
        """
        Vérifier si une notification similaire non lue existe déjà
        Évite les doublons de notifications
        
        Returns:
            True si un doublon existe
        """
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.categorie == categorie,
                Notification.message.contains(message_contains),
                Notification.is_read == False
            )
        )
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    async def notify_if_not_duplicate(
        db: AsyncSession,
        user_id: int,
        titre: str,
        message: str,
        type_notif: str = NotificationType.INFO,
        categorie: str = NotificationCategorie.GENERAL,
        chantier_id: int = None,
        duplicate_check_text: str = None
    ) -> Optional[Notification]:
        """
        Créer une notification seulement si aucun doublon n'existe
        
        Args:
            duplicate_check_text: Texte à rechercher pour détecter un doublon
                                  (par défaut: le message complet)
        """
        check_text = duplicate_check_text or message
        
        if await NotificationService.check_duplicate(db, user_id, categorie, check_text):
            return None
        
        return await NotificationService.notify_user(
            db=db,
            user_id=user_id,
            titre=titre,
            message=message,
            type_notif=type_notif,
            categorie=categorie,
            chantier_id=chantier_id
        )
