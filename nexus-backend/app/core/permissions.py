"""
NEXUS GROUP - Permissions Module
=================================
Gestion des permissions RBAC selon les 8 rôles définis
"""

from fastapi import HTTPException, Depends, status
from typing import List, Optional
from app.core.security import get_current_user, RoleEnum, get_role_level


# =============================================================================
# DÉFINITION DES PERMISSIONS PAR RÔLE (8 rôles)
# =============================================================================

ROLE_PERMISSIONS = {
    
    # =========================================================================
    # 1. ADMINISTRATEUR GÉNÉRAL - Accès total ⛔️ Aucune restriction
    # =========================================================================
    RoleEnum.ADMIN_GENERAL: [
        "all"  # Accès total à toutes les permissions
    ],
    
    # =========================================================================
    # 2. ADMINISTRATEUR DE CHANTIER - Rôle intermédiaire délégué
    # =========================================================================
    RoleEnum.ADMIN_CHANTIER: [
        # Chantiers (ses chantiers assignés uniquement)
        "view_chantiers", "view_chantiers_assignes", "edit_chantier",
        
        # Tâches
        "view_taches", "create_tache", "edit_tache", "delete_tache", "assign_tache",
        
        # Journal de chantier
        "view_journal", "create_journal", "edit_journal",
        
        # Documents
        "view_documents", "upload_document", "delete_document", "download_document",
        "validate_document_client",  # Valider docs pour le client
        
        # Employés (lecture)
        "view_employes",
        
        # Présences / Pointage
        "view_presences", "manage_presences",
        
        # Finance (consultation chantier, pas modification globale)
        "view_budget_chantier",
        
        # Dépenses (voir, pas valider final)
        "view_depenses",
        
        # Commandes - Validation intermédiaire
        "view_commandes", "validate_commande_chantier",
        
        # Stock du chantier
        "view_stock", "view_stock_chantier",
        
        # Équipements
        "view_equipements", "view_equipements_chantier",
        
        # Modifications - Valider les propositions chef chantier
        "validate_modification",
        
        # Rapports du chantier
        "view_rapports", "view_rapports_chantier", "view_rapports_techniques",
        
        # Notifications
        "view_notifications",
    ],
    
    # =========================================================================
    # 3. COMPTABLE / FINANCIER - Accès financier uniquement
    # =========================================================================
    RoleEnum.COMPTABLE: [
        # Chantiers (lecture pour contexte)
        "view_chantiers", "view_all_chantiers",
        
        # ⛔️ PAS de tâches, PAS de planning
        
        # Documents techniques (lecture seule)
        "view_documents", "view_documents_techniques", "download_document",
        
        # Budget complet
        "view_budget", "view_budget_global", "view_budget_chantier",
        "view_previsions",
        "export_budget",
        
        # Dépenses
        "view_depenses", "view_all_depenses", "create_depense",
        
        # Paiements ouvriers
        "view_paiements", "create_paiement", "manage_paiements",
        
        # Factures fournisseurs
        "view_factures", "create_facture", "manage_factures",
        
        # Avances et soldes
        "view_avances", "manage_avances",
        
        # Employés (pour salaires)
        "view_employes", "view_all_employes", "view_salaires",
        
        # Export PDF/Excel
        "export_rapports", "export_finances",
        
        # Rapports financiers
        "view_rapports", "view_rapports_financiers",
        
        # Notifications
        "view_notifications",
    ],
    
    # =========================================================================
    # 4. CHEF DE CHANTIER / CONDUCTEUR DE TRAVAUX - Opérationnel terrain
    # =========================================================================
    RoleEnum.CHEF_CHANTIER: [
        # Chantiers (ses chantiers assignés)
        "view_chantiers", "view_chantiers_assignes",
        
        # Tâches - Création et mise à jour
        "view_taches", "create_tache", "edit_tache", "assign_tache",
        "update_avancement",
        
        # Journal de chantier
        "view_journal", "create_journal", "edit_journal",
        
        # Documents - Upload photos/vidéos/documents
        "view_documents", "upload_document", "download_document",
        
        # Employés (lecture)
        "view_employes",
        
        # Pointage des ouvriers
        "view_presences", "create_presence", "manage_presences",
        
        # ⛔️ PAS d'accès aux budgets globaux
        # ⛔️ PAS de validation financière
        
        # Stock du chantier (consultation)
        "view_stock", "view_stock_chantier",
        
        # Matériel affecté
        "view_equipements", "view_equipements_chantier", "manage_equipements",
        
        # Demandes (matériaux, équipements)
        "view_commandes", "create_commande", "create_demande_equipement",
        
        # Propositions de modifications (validation Admin requise)
        "propose_modification",
        
        # Rapports du chantier
        "view_rapports", "view_rapports_chantier",
        
        # Notifications
        "view_notifications",
    ],
    
    # =========================================================================
    # 5. MAGASINIER / GESTIONNAIRE DE STOCK
    # =========================================================================
    RoleEnum.MAGASINIER: [
        # Chantiers (pour contexte)
        "view_chantiers", "view_all_chantiers",
        
        # ⛔️ PAS d'accès aux budgets
        # ⛔️ PAS d'accès aux données RH
        
        # Stock - Gestion complète
        "view_stock", "view_all_stock",
        "create_stock", "edit_stock", "delete_stock",
        "mouvement_stock",          # Entrées/sorties
        "receive_materiel",         # Réception matériaux
        "transfer_stock",           # Affectation aux chantiers
        "view_historique_stock",    # Historique mouvements
        
        # Équipements
        "view_equipements", "manage_equipements",
        
        # Commandes (validation logistique, pas financière)
        "view_commandes",
        
        # Documents (bons de livraison, etc.)
        "view_documents", "upload_document", "download_document",
        
        # Notifications
        "view_notifications",
    ],
    
    # =========================================================================
    # 6. OUVRIER / TECHNICIEN - Accès très limité
    # =========================================================================
    RoleEnum.OUVRIER: [
        # ⛔️ Aucun accès aux documents sensibles
        # ⛔️ Aucun accès financier
        # Lecture + saisie minimale uniquement
        
        # Tâches assignées seulement
        "view_taches_assignees",
        "update_avancement",
        
        # Pointage personnel (entrée/sortie)
        "view_presence_personnelle",
        "pointer",
        
        # Notifications (tâches assignées)
        "view_notifications",
    ],
    
    # =========================================================================
    # 7. CLIENT - Accès consultatif et transparent
    # =========================================================================
    RoleEnum.CLIENT: [
        # ⛔️ Aucun accès aux budgets internes
        # ⛔️ Aucun accès RH
        # ⛔️ Aucun accès aux documents non validés
        
        # Son chantier uniquement
        "view_chantier_propre",
        
        # Avancement global
        "view_avancement",
        "view_photos_validees",
        "view_videos_validees",
        "add_commentaire",
        "view_historique_etapes",
        
        # Documents validés seulement
        "view_documents_valides",
        "download_document",
        
        # Notifications
        "view_notifications",
    ],
    
    # =========================================================================
    # 8. DIRECTION / ASSOCIÉ - Lecture seule supervision
    # =========================================================================
    RoleEnum.DIRECTION: [
        # ⛔️ AUCUNE MODIFICATION POSSIBLE - Lecture seule
        
        # Tous les chantiers (lecture)
        "view_chantiers", "view_all_chantiers",
        
        # Tâches (lecture)
        "view_taches",
        
        # Journal (lecture)
        "view_journal",
        
        # Documents (lecture)
        "view_documents", "download_document",
        
        # Employés (lecture avec salaires)
        "view_employes", "view_all_employes", "view_salaires",
        
        # Pointage (lecture)
        "view_presences", "view_all_presences",
        
        # Budget complet (lecture)
        "view_budget", "view_budget_global", "view_budget_chantier",
        "view_previsions",
        
        # Dépenses (lecture)
        "view_depenses", "view_all_depenses",
        
        # Paiements (lecture)
        "view_paiements",
        
        # Factures (lecture)
        "view_factures",
        
        # Stock (lecture)
        "view_stock", "view_all_stock", "view_historique_stock",
        
        # Commandes (lecture)
        "view_commandes",
        
        # Tous les rapports (lecture)
        "view_rapports", "view_rapports_financiers",
        "view_rapports_techniques", "view_rapports_rh",
        
        # Dashboard global
        "view_dashboard_global",
        
        # Audit (lecture)
        "view_audit",
        
        # Notifications
        "view_notifications",
    ],
}


# =============================================================================
# PERMISSIONS NÉCESSITANT VALIDATION ADMIN
# =============================================================================

REQUIRES_ADMIN_VALIDATION = [
    "approve_depense",           # Validation finale dépenses
    "validate_commande_final",   # Validation finale commandes
    "validate_modification",     # Validation modifications sensibles
    "validate_document_client",  # Documents visibles par client
    "edit_budget_global",        # Modification budget global
    "delete_employe",            # Suppression employé
    "change_role",               # Changement de rôle
]


# =============================================================================
# ACTIONS AUDITÉES (qui a fait quoi, quand)
# =============================================================================

AUDITED_ACTIONS = [
    "create_user", "edit_user", "delete_user", "change_role",
    "approve_depense", "validate_commande_final",
    "edit_budget_global", "edit_budget_chantier",
    "validate_document_client", "delete_document",
    "transfer_stock", "mouvement_stock",
    "create_paiement",
    "validate_modification",
]


# =============================================================================
# FONCTIONS DE VÉRIFICATION DES PERMISSIONS
# =============================================================================

def has_permission(role: str, permission: str) -> bool:
    """
    Vérifie si un rôle a une permission spécifique
    
    Args:
        role: Le rôle de l'utilisateur
        permission: La permission à vérifier
    
    Returns:
        True si le rôle a la permission
    """
    # Admin général a toutes les permissions
    if role == RoleEnum.ADMIN_GENERAL:
        return True
    
    permissions = ROLE_PERMISSIONS.get(role, [])
    return permission in permissions or "all" in permissions


def has_any_permission(role: str, permissions: List[str]) -> bool:
    """Vérifie si un rôle a au moins une des permissions"""
    return any(has_permission(role, perm) for perm in permissions)


def has_all_permissions(role: str, permissions: List[str]) -> bool:
    """Vérifie si un rôle a toutes les permissions"""
    return all(has_permission(role, perm) for perm in permissions)


def get_role_permissions(role: str) -> List[str]:
    """Retourne la liste des permissions d'un rôle"""
    if role == RoleEnum.ADMIN_GENERAL:
        # Retourner toutes les permissions uniques
        all_perms = set()
        for perms in ROLE_PERMISSIONS.values():
            all_perms.update(perms)
        all_perms.discard("all")
        return list(all_perms)
    
    return ROLE_PERMISSIONS.get(role, [])


def is_read_only_role(role: str) -> bool:
    """Vérifie si le rôle est en lecture seule (Direction)"""
    return role == RoleEnum.DIRECTION


def requires_admin_validation(permission: str) -> bool:
    """Vérifie si une permission nécessite validation admin"""
    return permission in REQUIRES_ADMIN_VALIDATION


def is_audited_action(action: str) -> bool:
    """Vérifie si une action doit être auditée"""
    return action in AUDITED_ACTIONS


# =============================================================================
# DÉCORATEURS FASTAPI
# =============================================================================

def require_permission(permission: str):
    """
    Décorateur pour vérifier une permission spécifique
    
    Usage:
        @router.get("/depenses")
        async def list_depenses(user = Depends(require_permission("view_depenses"))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role", RoleEnum.OUVRIER)
        
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée. Rôle '{role}' n'a pas la permission '{permission}'"
            )
        return user
    
    return dependency


def require_any_permission(*permissions):
    """
    Décorateur pour vérifier au moins une permission parmi plusieurs
    
    Usage:
        @router.get("/finances")
        async def finances(user = Depends(require_any_permission("view_budget", "view_depenses"))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role", RoleEnum.OUVRIER)
        
        if not has_any_permission(role, list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée. Aucune des permissions requises: {', '.join(permissions)}"
            )
        return user
    
    return dependency


def require_all_permissions(*permissions):
    """
    Décorateur pour vérifier toutes les permissions
    
    Usage:
        @router.delete("/employes/{id}")
        async def delete(user = Depends(require_all_permissions("view_employes", "delete_employe"))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role", RoleEnum.OUVRIER)
        
        if not has_all_permissions(role, list(permissions)):
            missing = [p for p in permissions if not has_permission(role, p)]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions manquantes: {', '.join(missing)}"
            )
        return user
    
    return dependency


def require_roles(*roles):
    """
    Décorateur pour vérifier les rôles autorisés
    
    Usage:
        @router.post("/users")
        async def create_user(user = Depends(require_roles("admin_general"))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        user_role = user.get("role", RoleEnum.OUVRIER)
        
        # Admin général a toujours accès
        if user_role == RoleEnum.ADMIN_GENERAL:
            return user
        
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles: {', '.join(roles)}"
            )
        return user
    
    return dependency


def require_admin():
    """
    Décorateur pour exiger le rôle Admin Général
    
    Usage:
        @router.delete("/users/{id}")
        async def delete_user(user = Depends(require_admin())):
            ...
    """
    return require_roles(RoleEnum.ADMIN_GENERAL)


def require_admin_or_admin_chantier():
    """Décorateur pour exiger Admin Général ou Admin Chantier"""
    return require_roles(RoleEnum.ADMIN_GENERAL, RoleEnum.ADMIN_CHANTIER)


def require_not_read_only():
    """
    Décorateur pour interdire les modifications au rôle Direction
    
    Usage:
        @router.put("/chantiers/{id}")
        async def update(user = Depends(require_not_read_only())):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role", RoleEnum.OUVRIER)
        
        if is_read_only_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Le rôle Direction est en lecture seule. Aucune modification autorisée."
            )
        return user
    
    return dependency


def require_chantier_access(chantier_id: int):
    """
    Décorateur pour vérifier l'accès à un chantier spécifique
    
    Usage:
        @router.get("/chantiers/{chantier_id}")
        async def get_chantier(chantier_id: int, user = Depends(require_chantier_access(chantier_id))):
            ...
    
    Note: Pour utiliser avec un paramètre de route, voir require_chantier_access_dynamic
    """
    def dependency(user: dict = Depends(get_current_user)):
        role = user.get("role", RoleEnum.OUVRIER)
        
        # Rôles avec accès global
        if role in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, 
                    RoleEnum.COMPTABLE, RoleEnum.MAGASINIER]:
            return user
        
        # Vérifier chantiers assignés
        chantiers_assignes = user.get("chantiers_assignes", [])
        if chantier_id not in chantiers_assignes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous n'avez pas accès au chantier #{chantier_id}"
            )
        
        return user
    
    return dependency


# =============================================================================
# FILTRAGE DES DONNÉES PAR RÔLE
# =============================================================================

class DataFilter:
    """Classe utilitaire pour filtrer les données selon le rôle"""
    
    @staticmethod
    def filter_chantiers(user: dict, chantiers: list) -> list:
        """
        Filtre les chantiers selon le rôle de l'utilisateur
        
        - Admin, Direction, Comptable, Magasinier: tous les chantiers
        - Client: son chantier uniquement
        - Autres: chantiers assignés
        """
        role = user.get("role", RoleEnum.OUVRIER)
        user_id = user.get("user_id")
        
        # Accès global
        if role in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION,
                    RoleEnum.COMPTABLE, RoleEnum.MAGASINIER]:
            return chantiers
        
        # Client: son chantier
        if role == RoleEnum.CLIENT:
            return [c for c in chantiers if c.get("client_id") == user_id]
        
        # Autres: chantiers assignés
        chantiers_assignes = user.get("chantiers_assignes", [])
        return [c for c in chantiers if c.get("id") in chantiers_assignes]
    
    @staticmethod
    def filter_employes(user: dict, employes: list) -> list:
        """
        Filtre les employés et masque les salaires si pas autorisé
        """
        role = user.get("role", RoleEnum.OUVRIER)
        
        # Peut voir les salaires
        if has_permission(role, "view_salaires"):
            return employes
        
        # Masquer les salaires
        filtered = []
        for emp in employes:
            emp_copy = emp.copy()
            emp_copy.pop("salaire", None)
            emp_copy.pop("salaire_journalier", None)
            emp_copy.pop("info_bancaire", None)
            filtered.append(emp_copy)
        return filtered
    
    @staticmethod
    def filter_documents(user: dict, documents: list) -> list:
        """
        Filtre les documents selon le rôle
        
        - Client: documents validés seulement
        - Comptable: documents techniques/financiers
        - Autres: tous les documents
        """
        role = user.get("role", RoleEnum.OUVRIER)
        
        # Client: seulement documents validés
        if role == RoleEnum.CLIENT:
            return [d for d in documents if d.get("valide_client", False)]
        
        # Comptable: documents techniques en lecture
        if role == RoleEnum.COMPTABLE:
            types_autorises = ["facture", "bon_livraison", "devis", "contrat"]
            return [d for d in documents if d.get("type") in types_autorises]
        
        return documents
    
    @staticmethod
    def filter_taches(user: dict, taches: list) -> list:
        """
        Filtre les tâches selon le rôle
        
        - Ouvrier: ses tâches assignées uniquement
        - Autres: toutes les tâches
        """
        role = user.get("role", RoleEnum.OUVRIER)
        user_id = user.get("user_id")
        
        # Ouvrier: ses tâches seulement
        if role == RoleEnum.OUVRIER:
            return [t for t in taches if t.get("assigne_a") == user_id]
        
        return taches
    
    @staticmethod
    def filter_depenses(user: dict, depenses: list) -> list:
        """
        Filtre les dépenses selon le rôle
        """
        role = user.get("role", RoleEnum.OUVRIER)
        
        # Pas d'accès aux dépenses
        if not has_permission(role, "view_depenses"):
            return []
        
        return depenses
    
    @staticmethod
    def filter_presences(user: dict, presences: list) -> list:
        """
        Filtre les présences selon le rôle
        
        - Ouvrier: sa présence personnelle uniquement
        - Autres: selon permissions
        """
        role = user.get("role", RoleEnum.OUVRIER)
        user_id = user.get("user_id")
        
        # Ouvrier: sa présence seulement
        if role == RoleEnum.OUVRIER:
            return [p for p in presences if p.get("employe_id") == user_id]
        
        return presences


# =============================================================================
# UTILITAIRES
# =============================================================================

def can_create_user(creator_role: str, new_user_role: str) -> bool:
    """
    Vérifie si un rôle peut créer un utilisateur avec un autre rôle
    Seul l'admin général peut créer des comptes
    """
    # Seul admin général peut créer des comptes
    if creator_role != RoleEnum.ADMIN_GENERAL:
        return False
    
    return True


def can_modify_user(modifier_role: str, target_role: str) -> bool:
    """
    Vérifie si un rôle peut modifier un utilisateur
    Un rôle ne peut modifier que des rôles de niveau inférieur
    """
    if modifier_role == RoleEnum.ADMIN_GENERAL:
        return True
    
    modifier_level = get_role_level(modifier_role)
    target_level = get_role_level(target_role)
    
    return modifier_level > target_level


def can_delete_user(deleter_role: str) -> bool:
    """
    Vérifie si un rôle peut supprimer un utilisateur
    Seul l'admin général peut supprimer
    """
    return deleter_role == RoleEnum.ADMIN_GENERAL


def can_change_role(changer_role: str, new_role: str) -> bool:
    """
    Vérifie si un rôle peut attribuer un autre rôle
    Seul l'admin général peut changer les rôles
    """
    return changer_role == RoleEnum.ADMIN_GENERAL