"""
NEXUS GROUP - Authentication Endpoints
========================================
Gestion de l'authentification et des utilisateurs
Seul l'admin général peut créer des comptes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    create_refresh_token,
    create_token,
    get_current_user,
    decode_token,
    RoleEnum,
    ROLE_INFO,
    get_role_info
)
from app.core.permissions import (
    require_roles, 
    require_admin,
    require_permission,
    can_create_user,
    can_modify_user,
    can_change_role,
    DataFilter
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


# =============================================================================
# LISTE DES RÔLES VALIDES (8 rôles)
# =============================================================================

VALID_ROLES = [
    RoleEnum.ADMIN_GENERAL,
    RoleEnum.ADMIN_CHANTIER,
    RoleEnum.COMPTABLE,
    RoleEnum.CHEF_CHANTIER,
    RoleEnum.MAGASINIER,
    RoleEnum.OUVRIER,
    RoleEnum.CLIENT,
    RoleEnum.DIRECTION,
]


# =============================================================================
# INSCRIPTION - Seul l'Admin Général peut créer des comptes
# =============================================================================

@router.post("/register", response_model=UserResponse)
async def register(
    data: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin())  # ✅ Seul admin peut créer
):
    """
    Créer un nouveau compte utilisateur
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut créer des comptes
    
    - Vérifie que l'email n'existe pas déjà
    - Vérifie que le rôle est valide
    - L'admin ne peut pas créer un autre admin_general
    """
    
    # Vérifier que l'admin peut créer ce rôle
    if not can_create_user(current_user.get("role"), data.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de créer des utilisateurs"
        )
    
    # Empêcher la création d'un autre admin_general (sauf par lui-même pour un premier setup)
    if data.role == RoleEnum.ADMIN_GENERAL:
        # Vérifier s'il existe déjà un admin_general
        result = await db.execute(
            select(User).where(User.role == RoleEnum.ADMIN_GENERAL)
        )
        existing_admin = result.scalar_one_or_none()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un Administrateur Général existe déjà. Impossible d'en créer un autre."
            )
    
    # Vérifier que le rôle est valide
    if data.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rôle invalide. Choix possibles: {', '.join(VALID_ROLES)}"
        )
    
    # Vérifier que l'email n'existe pas
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cet email est déjà utilisé"
        )
    
    # Vérifier le téléphone s'il est fourni
    if data.phone:
        result = await db.execute(select(User).where(User.phone == data.phone))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce numéro de téléphone est déjà utilisé"
            )
    
    # Créer l'utilisateur
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=data.role,
        chantier_id=data.chantier_id,
        is_active=True,
        
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # TODO: Logger l'action pour audit
    # await log_audit(db, current_user, "create_user", user.id)
    
    return user


# =============================================================================
# PREMIER ADMIN - Route spéciale pour créer le premier admin (sans auth)
# =============================================================================

@router.post("/setup-admin", response_model=UserResponse)
async def setup_first_admin(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Créer le premier Administrateur Général
    
    ⚠️ Cette route ne fonctionne QUE s'il n'existe aucun admin_general
    Elle est destinée à l'installation initiale uniquement
    """
    
    # Vérifier qu'aucun admin n'existe
    result = await db.execute(
        select(User).where(User.role == RoleEnum.ADMIN_GENERAL)
    )
    existing_admin = result.scalar_one_or_none()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Un Administrateur Général existe déjà. Utilisez /register avec authentification."
        )
    
    # Vérifier que l'email n'existe pas
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    # Forcer le rôle admin_general
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        role=RoleEnum.ADMIN_GENERAL,  # Forcé
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


# =============================================================================
# CONNEXION
# =============================================================================

@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    Connexion utilisateur
    
    Retourne un token JWT contenant:
    - user_id
    - email
    - role
    - nom, prénom
    - chantiers_assignes (liste des IDs)
    """
    
    # Chercher l'utilisateur
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    
    # Vérifier les credentials
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Vérifier si le compte est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Votre compte a été désactivé. Contactez l'administrateur."
        )
    
    # Récupérer les chantiers assignés
    chantiers_assignes = []
    if user.chantier_id:
        chantiers_assignes = [user.chantier_id]
    # TODO: Si l'utilisateur peut avoir plusieurs chantiers, adapter ici
    # chantiers_assignes = await get_user_chantiers(db, user.id)
    
    # Créer le token avec toutes les infos nécessaires
    token_data = {
        "user_id": user.id,
        "sub": str(user.id),  # Pour compatibilité OAuth2
        "email": user.email,
        "role": user.role,
        "nom": user.last_name,
        "prenom": user.first_name,
        "chantiers_assignes": chantiers_assignes,
        "chantier_id": user.chantier_id  # Pour compatibilité
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user.id})
    
    # Mettre à jour la dernière connexion
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


# =============================================================================
# REFRESH TOKEN
# =============================================================================

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Rafraîchir le token d'accès avec le refresh token
    """
    try:
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresh invalide"
            )
        
        user_id = payload.get("user_id")
        
        # Récupérer l'utilisateur
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur invalide ou inactif"
            )
        
        # Récupérer les chantiers assignés
        chantiers_assignes = [user.chantier_id] if user.chantier_id else []
        
        # Créer un nouveau token
        token_data = {
            "user_id": user.id,
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "nom": user.last_name,
            "prenom": user.first_name,
            "chantiers_assignes": chantiers_assignes,
            "chantier_id": user.chantier_id
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"user_id": user.id})
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalide ou expiré"
        )


# =============================================================================
# PROFIL UTILISATEUR CONNECTÉ
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def me(
    current_user: dict = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Récupérer le profil de l'utilisateur connecté
    """
    user_id = current_user.get("user_id") or int(current_user.get("sub", 0))
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Utilisateur non trouvé"
        )
    
    return user


# =============================================================================
# INFORMATIONS SUR LE RÔLE
# =============================================================================

@router.get("/me/permissions")
async def my_permissions(current_user: dict = Depends(get_current_user)):
    """
    Récupérer les permissions de l'utilisateur connecté
    Utile pour le frontend pour adapter l'interface
    """
    from app.core.permissions import get_role_permissions
    
    role = current_user.get("role", RoleEnum.OUVRIER)
    role_info = get_role_info(role)
    permissions = get_role_permissions(role)
    
    return {
        "user_id": current_user.get("user_id"),
        "role": role,
        "role_info": role_info,
        "permissions": permissions,
        "chantiers_assignes": current_user.get("chantiers_assignes", [])
    }


# =============================================================================
# LISTE DES UTILISATEURS (Admin seulement)
# =============================================================================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("view_all_employes"))
):
    """
    Liste tous les utilisateurs
    
    Accès: Admin Général, Comptable (pour salaires), Direction (lecture)
    """
    role = current_user.get("role")
    
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    # Filtrer les données sensibles selon le rôle
    users_list = [user.__dict__ for user in users]
    filtered_users = DataFilter.filter_employes(current_user, users_list)
    
    return filtered_users


# =============================================================================
# MODIFIER LE RÔLE D'UN UTILISATEUR (Admin seulement)
# =============================================================================

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin())  # ✅ Seul admin
):
    """
    Modifier le rôle d'un utilisateur
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut changer les rôles
    """
    
    # Vérifier que l'admin peut changer le rôle
    if not can_change_role(current_user.get("role"), role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de modifier les rôles"
        )
    
    # Récupérer l'utilisateur
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher de modifier son propre rôle
    current_user_id = current_user.get("user_id") or int(current_user.get("sub", 0))
    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas modifier votre propre rôle"
        )
    
    # Empêcher de modifier un autre admin_general
    if user.role == RoleEnum.ADMIN_GENERAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de modifier le rôle de l'Administrateur Général"
        )
    
    # Vérifier que le nouveau rôle est valide
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Rôle invalide. Choix: {', '.join(VALID_ROLES)}"
        )
    
    # Empêcher de créer un nouveau admin_general
    if role == RoleEnum.ADMIN_GENERAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de promouvoir un utilisateur en Administrateur Général"
        )
    
    # Mettre à jour
    old_role = user.role
    user.role = role
    if chantier_id is not None:
        user.chantier_id = chantier_id
    
    await db.commit()
    
    # TODO: Logger l'action pour audit
    # await log_audit(db, current_user, "change_role", user.id, {"old_role": old_role, "new_role": role})
    
    return {
        "message": f"Rôle mis à jour: {old_role} → {role}",
        "user_id": user.id,
        "new_role": role,
        "role_info": get_role_info(role)
    }


# =============================================================================
# DÉSACTIVER UN UTILISATEUR (Admin seulement)
# =============================================================================

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin())
):
    """
    Désactiver un compte utilisateur
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut désactiver des comptes
    """
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher de se désactiver soi-même
    current_user_id = current_user.get("user_id") or int(current_user.get("sub", 0))
    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
    
    # Empêcher de désactiver un admin_general
    if user.role == RoleEnum.ADMIN_GENERAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de désactiver l'Administrateur Général"
        )
    
    user.is_active = False
    await db.commit()
    
    return {"message": f"Compte de {user.email} désactivé"}


# =============================================================================
# RÉACTIVER UN UTILISATEUR (Admin seulement)
# =============================================================================

@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin())
):
    """
    Réactiver un compte utilisateur
    """
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    user.is_active = True
    await db.commit()
    
    return {"message": f"Compte de {user.email} réactivé"}


# =============================================================================
# LISTE DES RÔLES DISPONIBLES
# =============================================================================

@router.get("/roles")
async def list_roles(current_user: dict = Depends(get_current_user)):
    """
    Liste tous les rôles disponibles avec leurs informations
    Utile pour les formulaires de création/modification d'utilisateur
    """
    
    roles = []
    for role in VALID_ROLES:
        info = get_role_info(role)
        roles.append({
            "code": role,
            "name": info.get("name", role),
            "description": info.get("description", ""),
            "color": info.get("color", "#000000"),
            "icon": info.get("icon", "👤"),
            "level": info.get("level", 0)
        })
    
    # Trier par niveau décroissant
    roles.sort(key=lambda x: x["level"], reverse=True)
    
    return roles


# =============================================================================
# CHANGER SON MOT DE PASSE
# =============================================================================

@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Changer son propre mot de passe
    """
    
    user_id = current_user.get("user_id") or int(current_user.get("sub", 0))
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Vérifier l'ancien mot de passe
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Valider le nouveau mot de passe
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 8 caractères"
        )
    
    # Mettre à jour
    user.hashed_password = hash_password(new_password)
    await db.commit()
    
    return {"message": "Mot de passe modifié avec succès"}
