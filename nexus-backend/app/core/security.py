"""
NEXUS GROUP - Security Module
==============================
Gestion de l'authentification et des tokens JWT
"""

from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import secrets


# =============================================================================
# CONFIGURATION
# =============================================================================

# ⚠️ EN PRODUCTION : Utiliser une variable d'environnement !
# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "nexus-secret-key-2024-super-secure-do-not-share"
ALGORITHM = "HS256"

# Durées des tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30      # Token d'accès : 30 min
REFRESH_TOKEN_EXPIRE_DAYS = 7         # Token de refresh : 7 jours

# Configuration du hachage de mot de passe
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Coût de hachage (plus élevé = plus sécurisé mais plus lent)
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# =============================================================================
# DÉFINITION DES RÔLES (8 rôles selon spécifications)
# =============================================================================

class RoleEnum:
    """Énumération des rôles disponibles"""
    
    ADMIN_GENERAL = "admin_general"       # 1. Accès total
    ADMIN_CHANTIER = "admin_chantier"     # 2. Rôle intermédiaire délégué
    COMPTABLE = "comptable"               # 3. Accès financier uniquement
    CHEF_CHANTIER = "chef_chantier"       # 4. Accès opérationnel terrain
    MAGASINIER = "magasinier"             # 5. Gestionnaire de stock
    OUVRIER = "ouvrier"                   # 6. Accès très limité
    CLIENT = "client"                     # 7. Accès consultatif
    DIRECTION = "direction"               # 8. Lecture seule supervision
    
    @classmethod
    def all_roles(cls) -> List[str]:
        """Retourne tous les rôles"""
        return [
            cls.ADMIN_GENERAL, cls.ADMIN_CHANTIER, cls.COMPTABLE,
            cls.CHEF_CHANTIER, cls.MAGASINIER, cls.OUVRIER,
            cls.CLIENT, cls.DIRECTION
        ]
    
    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Vérifie si un rôle est valide"""
        return role in cls.all_roles()


# Informations des rôles (pour affichage)
ROLE_INFO = {
    RoleEnum.ADMIN_GENERAL: {
        "name": "Administrateur Général",
        "description": "Accès total au système",
        "color": "#8B0000",
        "icon": "👑",
        "level": 10
    },
    RoleEnum.ADMIN_CHANTIER: {
        "name": "Administrateur de Chantier",
        "description": "Rôle intermédiaire pour déléguer",
        "color": "#1a1a2e",
        "icon": "🏗️",
        "level": 8
    },
    RoleEnum.COMPTABLE: {
        "name": "Comptable / Financier",
        "description": "Accès financier uniquement",
        "color": "#cc6600",
        "icon": "💰",
        "level": 6
    },
    RoleEnum.CHEF_CHANTIER: {
        "name": "Chef de Chantier",
        "description": "Accès opérationnel terrain",
        "color": "#006400",
        "icon": "👷",
        "level": 5
    },
    RoleEnum.MAGASINIER: {
        "name": "Magasinier",
        "description": "Gestionnaire de stock",
        "color": "#666666",
        "icon": "📦",
        "level": 4
    },
    RoleEnum.OUVRIER: {
        "name": "Ouvrier / Technicien",
        "description": "Accès très limité",
        "color": "#336699",
        "icon": "🔧",
        "level": 2
    },
    RoleEnum.CLIENT: {
        "name": "Client",
        "description": "Accès consultatif",
        "color": "#4a90a4",
        "icon": "🏠",
        "level": 1
    },
    RoleEnum.DIRECTION: {
        "name": "Direction / Associé",
        "description": "Supervision lecture seule",
        "color": "#4a0080",
        "icon": "📊",
        "level": 9
    }
}


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class TokenData(BaseModel):
    """Données contenues dans le token JWT"""
    user_id: int
    email: str
    role: str
    nom: str
    prenom: str
    chantiers_assignes: List[int] = []  # IDs des chantiers assignés
    exp: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Réponse d'authentification"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Secondes
    user: dict


# =============================================================================
# FONCTIONS DE HACHAGE
# =============================================================================

def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# =============================================================================
# FONCTIONS DE GESTION DES TOKENS
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token d'accès JWT
    
    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité (défaut: 30 min)
    
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "type": "access"
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Crée un token de refresh JWT (longue durée)
    
    Args:
        data: Données minimales (user_id)
    
    Returns:
        Token JWT encodé
    """
    to_encode = {
        "user_id": data.get("user_id"),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_hex(16)  # ID unique du token
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_token(data: dict) -> str:
    """
    Fonction legacy pour compatibilité
    Crée un token d'accès de 24h
    """
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=24)
    to_encode["iat"] = datetime.utcnow()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Décode et valide un token JWT
    
    Args:
        token: Token JWT à décoder
    
    Returns:
        Payload du token
    
    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"}
        )


# =============================================================================
# DÉPENDANCES FASTAPI
# =============================================================================

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Récupère l'utilisateur courant depuis le token JWT
    
    Retourne un dictionnaire contenant:
    - user_id: ID de l'utilisateur
    - email: Email
    - role: Rôle de l'utilisateur
    - nom, prenom: Identité
    - chantiers_assignes: Liste des IDs de chantiers assignés
    
    Raises:
        HTTPException 401: Si le token est invalide
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        # Construire les données utilisateur
        user_data = {
            "user_id": user_id,
            "email": payload.get("email", ""),
            "role": payload.get("role", RoleEnum.OUVRIER),
            "nom": payload.get("nom", ""),
            "prenom": payload.get("prenom", ""),
            "chantiers_assignes": payload.get("chantiers_assignes", []),
        }
        
        return user_data
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Vérifie que l'utilisateur est actif
    À utiliser si vous avez un champ 'is_active' dans votre base
    """
    # Ici vous pouvez ajouter une vérification en base de données
    # pour voir si l'utilisateur est toujours actif
    return current_user


def get_optional_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """
    Récupère l'utilisateur si le token est valide, sinon retourne None
    Utile pour les routes accessibles avec ou sans authentification
    """
    try:
        return get_current_user(token)
    except HTTPException:
        return None


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_role_info(role: str) -> dict:
    """Retourne les informations d'un rôle"""
    return ROLE_INFO.get(role, {
        "name": role,
        "description": "Rôle inconnu",
        "color": "#000000",
        "icon": "👤",
        "level": 0
    })


def get_role_level(role: str) -> int:
    """Retourne le niveau hiérarchique d'un rôle"""
    info = get_role_info(role)
    return info.get("level", 0)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """
    Vérifie si un rôle peut gérer un autre rôle
    Un rôle peut gérer les rôles de niveau inférieur
    """
    manager_level = get_role_level(manager_role)
    target_level = get_role_level(target_role)
    return manager_level > target_level


def is_admin(role: str) -> bool:
    """Vérifie si le rôle est admin (général ou chantier)"""
    return role in [RoleEnum.ADMIN_GENERAL, RoleEnum.ADMIN_CHANTIER]


def is_admin_general(role: str) -> bool:
    """Vérifie si le rôle est admin général"""
    return role == RoleEnum.ADMIN_GENERAL


def is_read_only(role: str) -> bool:
    """Vérifie si le rôle est en lecture seule (Direction)"""
    return role == RoleEnum.DIRECTION


def has_chantier_access(user: dict, chantier_id: int) -> bool:
    """
    Vérifie si l'utilisateur a accès à un chantier spécifique
    
    - Admin Général: accès à tous
    - Direction: accès lecture à tous
    - Comptable: accès lecture à tous (pour finance)
    - Magasinier: accès lecture à tous (pour stock)
    - Autres: uniquement leurs chantiers assignés
    """
    role = user.get("role", "")
    
    # Accès global
    if role in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, 
                RoleEnum.COMPTABLE, RoleEnum.MAGASINIER]:
        return True
    
    # Vérifier assignation
    chantiers_assignes = user.get("chantiers_assignes", [])
    return chantier_id in chantiers_assignes


def generate_password_reset_token(email: str) -> str:
    """Génère un token de réinitialisation de mot de passe"""
    data = {
        "email": email,
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)  # Valide 1 heure
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Vérifie un token de réinitialisation et retourne l'email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("email")
    except JWTError:
        return None