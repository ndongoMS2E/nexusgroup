"""
NEXUS GROUP - Employés & Pointage Endpoints
=============================================
Gestion des employés et du pointage avec contrôle d'accès par rôle

Permissions:
- Admin Général: CRUD total + tous les salaires
- Admin Chantier: Voir employés de ses chantiers + pointage
- Comptable: Voir tous employés + salaires (pour paiements)
- Chef Chantier: Voir employés + gérer pointage de son chantier
- Direction: Lecture seule tous employés + salaires
- Magasinier: ❌ Pas d'accès RH
- Ouvrier: Voir SON pointage personnel uniquement
- Client: ❌ Pas d'accès RH
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime, date as date_type

from app.core.database import get_db
from app.core.security import get_current_user, RoleEnum, has_chantier_access
from app.core.permissions import (
    require_permission,
    require_admin,
    require_roles,
    has_permission,
    DataFilter
)
from app.models.employe import Employe, Presence
from app.schemas.employe import EmployeCreate, EmployeResponse, PresenceCreate, PresenceResponse

router = APIRouter(prefix="/employes", tags=["Employes"])


# =============================================================================
# SCHÉMAS
# =============================================================================

class EmployeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    poste: Optional[str] = None
    salaire_journalier: Optional[float] = None
    chantier_id: Optional[int] = None


class AffectationRequest(BaseModel):
    chantier_id: Optional[int] = None


class PointageMasse(BaseModel):
    employe_id: int
    status: str
    heures: Optional[float] = 8


# =============================================================================
# ===================== EMPLOYES =====================
# =============================================================================

@router.get("/", response_model=List[EmployeResponse])
async def list_employes(
    chantier_id: Optional[int] = Query(None, description="Filtrer par chantier"),
    poste: Optional[str] = Query(None, description="Filtrer par poste"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_employes"))
):
    """
    Liste des employés selon le rôle:
    
    - Admin Général, Comptable, Direction: Tous les employés
    - Admin Chantier, Chef Chantier: Employés de leurs chantiers
    - Magasinier, Ouvrier, Client: ❌ Pas d'accès
    
    ⚠️ Les salaires sont masqués pour ceux qui n'ont pas la permission "view_salaires"
    """
    role = user.get("role", RoleEnum.OUVRIER)
    chantiers_assignes = user.get("chantiers_assignes", [])
    user_chantier_id = user.get("chantier_id")
    
    query = select(Employe).where(Employe.is_active == True)
    
    # Filtrage par rôle
    if role in [RoleEnum.ADMIN_CHANTIER, RoleEnum.CHEF_CHANTIER]:
        # Seulement leurs chantiers
        if chantiers_assignes:
            query = query.where(Employe.chantier_id.in_(chantiers_assignes))
        elif user_chantier_id:
            query = query.where(Employe.chantier_id == user_chantier_id)
    
    # Filtre additionnel par chantier
    if chantier_id:
        # Vérifier l'accès
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès aux employés de ce chantier"
                )
        query = query.where(Employe.chantier_id == chantier_id)
    
    if poste:
        query = query.where(Employe.poste == poste)
    
    query = query.order_by(Employe.nom)
    result = await db.execute(query)
    employes = result.scalars().all()
    
    # Masquer les salaires si pas autorisé
    if not has_permission(role, "view_salaires"):
        employes_list = []
        for emp in employes:
            emp_dict = {
                "id": emp.id,
                "matricule": emp.matricule,
                "nom": emp.nom,
                "prenom": emp.prenom,
                "telephone": emp.telephone,
                "poste": emp.poste,
                "date_embauche": emp.date_embauche,
                "chantier_id": emp.chantier_id,
                "is_active": emp.is_active,
                # salaire_journalier est masqué
            }
            employes_list.append(emp_dict)
        return employes_list
    
    return employes


# =============================================================================
# EMPLOYÉS NON AFFECTÉS
# =============================================================================

@router.get("/non-affectes")
async def list_employes_non_affectes(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Liste des employés sans chantier assigné
    
    ⚠️ Admin seulement - pour l'affectation
    """
    query = select(Employe).where(
        Employe.is_active == True,
        Employe.chantier_id == None
    ).order_by(Employe.nom)
    
    result = await db.execute(query)
    return result.scalars().all()


# =============================================================================
# CRÉER UN EMPLOYÉ
# =============================================================================

@router.post("/", response_model=EmployeResponse)
async def create_employe(
    data: EmployeCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Créer un nouvel employé
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut créer des employés
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Générer un matricule unique
    matricule = f"EMP-{datetime.now().year}-{random.randint(1000,9999)}"
    
    # Vérifier unicité
    result = await db.execute(select(Employe).where(Employe.matricule == matricule))
    while result.scalar_one_or_none():
        matricule = f"EMP-{datetime.now().year}-{random.randint(1000,9999)}"
        result = await db.execute(select(Employe).where(Employe.matricule == matricule))
    
    employe = Employe(
        matricule=matricule,
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone,
        poste=data.poste,
        salaire_journalier=data.salaire_journalier,
        date_embauche=data.date_embauche,
        chantier_id=data.chantier_id,
        created_by=user_id
    )
    
    db.add(employe)
    await db.commit()
    await db.refresh(employe)
    
    return employe


# =============================================================================
# DÉTAIL D'UN EMPLOYÉ
# =============================================================================

@router.get("/{id}", response_model=EmployeResponse)
async def get_employe(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_employes"))
):
    """
    Récupérer les détails d'un employé
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    result = await db.execute(select(Employe).where(Employe.id == id))
    employe = result.scalar_one_or_none()
    
    if not employe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Employé non trouvé"
        )
    
    # Vérifier l'accès au chantier de l'employé
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
        if employe.chantier_id and not has_chantier_access(user, employe.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à cet employé"
            )
    
    # Masquer le salaire si pas autorisé
    if not has_permission(role, "view_salaires"):
        return {
            "id": employe.id,
            "matricule": employe.matricule,
            "nom": employe.nom,
            "prenom": employe.prenom,
            "telephone": employe.telephone,
            "poste": employe.poste,
            "date_embauche": employe.date_embauche,
            "chantier_id": employe.chantier_id,
            "is_active": employe.is_active
        }
    
    return employe


# =============================================================================
# MODIFIER UN EMPLOYÉ
# =============================================================================

@router.put("/{id}", response_model=EmployeResponse)
async def update_employe(
    id: int,
    data: EmployeUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Modifier un employé
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut modifier les employés
    """
    
    result = await db.execute(select(Employe).where(Employe.id == id))
    employe = result.scalar_one_or_none()
    
    if not employe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Employé non trouvé"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employe, field, value)
    
    employe.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(employe)
    
    return employe


# =============================================================================
# AFFECTER UN EMPLOYÉ À UN CHANTIER
# =============================================================================

@router.put("/{id}/affecter")
async def affecter_employe(
    id: int,
    data: AffectationRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Affecter ou désaffecter un employé à un chantier
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut affecter les employés
    """
    
    result = await db.execute(select(Employe).where(Employe.id == id))
    employe = result.scalar_one_or_none()
    
    if not employe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Employé non trouvé"
        )
    
    ancien_chantier = employe.chantier_id
    employe.chantier_id = data.chantier_id
    employe.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(employe)
    
    if data.chantier_id:
        return {
            "message": f"Employé {employe.nom} {employe.prenom} affecté au chantier {data.chantier_id}",
            "ancien_chantier": ancien_chantier,
            "nouveau_chantier": data.chantier_id
        }
    else:
        return {
            "message": f"Employé {employe.nom} {employe.prenom} désaffecté",
            "ancien_chantier": ancien_chantier
        }


# =============================================================================
# DÉSACTIVER UN EMPLOYÉ (au lieu de supprimer)
# =============================================================================

@router.delete("/{id}")
async def delete_employe(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_admin())  # ✅ Admin seulement
):
    """
    Désactiver un employé (soft delete)
    
    ⚠️ SÉCURITÉ: Seul l'Administrateur Général peut désactiver des employés
    """
    
    result = await db.execute(select(Employe).where(Employe.id == id))
    employe = result.scalar_one_or_none()
    
    if not employe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Employé non trouvé"
        )
    
    employe.is_active = False
    employe.deactivated_at = datetime.utcnow()
    employe.deactivated_by = user.get("user_id")
    
    await db.commit()
    
    return {"message": f"Employé {employe.nom} {employe.prenom} désactivé"}


# =============================================================================
# ===================== POINTAGE =====================
# =============================================================================

@router.get("/pointage/{chantier_id}/{date_pointage}")
async def get_pointage_jour(
    chantier_id: int,
    date_pointage: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_presences"))
):
    """
    Récupérer le pointage d'un jour pour un chantier
    
    Permissions:
    - Admin, Direction: Tous les chantiers
    - Admin Chantier, Chef Chantier: Leurs chantiers
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Vérifier l'accès au chantier
    if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.DIRECTION, RoleEnum.COMPTABLE]:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès au pointage de ce chantier"
            )
    
    # Convertir la date
    try:
        date_obj = datetime.strptime(date_pointage, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    # Récupérer tous les employés du chantier
    result = await db.execute(
        select(Employe).where(
            Employe.chantier_id == chantier_id,
            Employe.is_active == True
        ).order_by(Employe.nom)
    )
    employes = result.scalars().all()
    
    pointage_list = []
    for emp in employes:
        # Chercher la présence
        pres_result = await db.execute(
            select(Presence).where(
                Presence.employe_id == emp.id,
                Presence.date == date_obj
            )
        )
        presence = pres_result.scalar_one_or_none()
        
        emp_data = {
            "employe_id": emp.id,
            "nom": emp.nom,
            "prenom": emp.prenom,
            "matricule": emp.matricule,
            "poste": emp.poste,
            "status": presence.status if presence else "non_pointe",
            "heures": presence.heures_travaillees if presence else 8
        }
        
        # Ajouter salaire si autorisé
        if has_permission(role, "view_salaires"):
            emp_data["salaire_journalier"] = emp.salaire_journalier
        
        pointage_list.append(emp_data)
    
    return pointage_list


# =============================================================================
# ENREGISTRER UN POINTAGE
# =============================================================================

@router.post("/pointage/")
async def enregistrer_pointage(
    data: PresenceCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("create_presence"))
):
    """
    Enregistrer un pointage
    
    Permissions:
    - Admin, Admin Chantier, Chef Chantier: Pointer les employés
    - Ouvrier: Se pointer soi-même uniquement
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Ouvrier: peut seulement se pointer lui-même
    if role == RoleEnum.OUVRIER:
        # TODO: Vérifier que l'employe_id correspond à l'utilisateur
        # if data.employe_id != user_employe_id:
        #     raise HTTPException(status_code=403, detail="Vous ne pouvez pointer que vous-même")
        pass
    
    # Vérifier l'accès au chantier
    if role not in [RoleEnum.ADMIN_GENERAL]:
        if not has_chantier_access(user, data.chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Convertir la date
    if isinstance(data.date, str):
        date_obj = datetime.strptime(data.date, "%Y-%m-%d").date()
    else:
        date_obj = data.date
    
    # Vérifier si un pointage existe déjà
    result = await db.execute(
        select(Presence).where(
            Presence.employe_id == data.employe_id,
            Presence.date == date_obj
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.status = data.status
        existing.heures_travaillees = data.heures if hasattr(data, 'heures') else 8
        existing.chantier_id = data.chantier_id
        existing.updated_by = user_id
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
    
    presence = Presence(
        employe_id=data.employe_id,
        chantier_id=data.chantier_id,
        date=date_obj,
        status=data.status,
        heures_travaillees=data.heures if hasattr(data, 'heures') else 8,
        created_by=user_id
    )
    db.add(presence)
    await db.commit()
    await db.refresh(presence)
    
    return presence


# =============================================================================
# POINTAGE EN MASSE
# =============================================================================

@router.post("/pointage/masse/")
async def pointage_masse(
    chantier_id: int,
    date_pointage: str,
    pointages: List[PointageMasse],
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("manage_presences"))
):
    """
    Enregistrer plusieurs pointages en une seule requête
    
    Permissions:
    - Admin, Admin Chantier, Chef Chantier: Leurs chantiers
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # Vérifier l'accès au chantier
    if role != RoleEnum.ADMIN_GENERAL:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
    
    # Convertir la date
    try:
        date_obj = datetime.strptime(date_pointage, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Format de date invalide"
        )
    
    count = 0
    for p in pointages:
        result = await db.execute(
            select(Presence).where(
                Presence.employe_id == p.employe_id,
                Presence.date == date_obj
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.status = p.status
            existing.heures_travaillees = p.heures or 8
            existing.updated_by = user_id
        else:
            presence = Presence(
                employe_id=p.employe_id,
                chantier_id=chantier_id,
                date=date_obj,
                status=p.status,
                heures_travaillees=p.heures or 8,
                created_by=user_id
            )
            db.add(presence)
        count += 1
    
    await db.commit()
    
    return {"message": f"{count} pointages enregistrés pour le {date_pointage}"}


# =============================================================================
# LISTE DES PRÉSENCES
# =============================================================================

@router.get("/presences/", response_model=List[PresenceResponse])
async def list_presences(
    chantier_id: Optional[int] = None,
    employe_id: Optional[int] = None,
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_presences"))
):
    """
    Liste des présences avec filtres
    
    - Ouvrier: Seulement ses propres présences
    """
    role = user.get("role", RoleEnum.OUVRIER)
    user_id = user.get("user_id")
    
    query = select(Presence)
    
    # Ouvrier: seulement ses présences
    if role == RoleEnum.OUVRIER:
        # TODO: Récupérer l'employe_id lié à l'utilisateur
        # query = query.where(Presence.employe_id == user_employe_id)
        pass
    
    # Filtres
    if chantier_id:
        if role not in [RoleEnum.ADMIN_GENERAL, RoleEnum.COMPTABLE, RoleEnum.DIRECTION]:
            if not has_chantier_access(user, chantier_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Vous n'avez pas accès à ce chantier"
                )
        query = query.where(Presence.chantier_id == chantier_id)
    
    if employe_id:
        query = query.where(Presence.employe_id == employe_id)
    
    if date_debut:
        date_debut_obj = datetime.strptime(date_debut, "%Y-%m-%d").date()
        query = query.where(Presence.date >= date_debut_obj)
    
    if date_fin:
        date_fin_obj = datetime.strptime(date_fin, "%Y-%m-%d").date()
        query = query.where(Presence.date <= date_fin_obj)
    
    query = query.order_by(Presence.date.desc())
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# MON POINTAGE PERSONNEL (Ouvrier)
# =============================================================================

@router.get("/mon-pointage/")
async def get_mon_pointage(
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_presence_personnelle"))
):
    """
    Récupérer son propre pointage (pour les ouvriers)
    """
    user_id = user.get("user_id") or int(user.get("sub", 0))
    
    # TODO: Récupérer l'employe_id lié à l'utilisateur
    # Pour l'instant, on suppose que user_id == employe_id ou qu'il y a une table de liaison
    
    query = select(Presence)  # .where(Presence.employe_id == user_employe_id)
    
    if date_debut:
        date_debut_obj = datetime.strptime(date_debut, "%Y-%m-%d").date()
        query = query.where(Presence.date >= date_debut_obj)
    
    if date_fin:
        date_fin_obj = datetime.strptime(date_fin, "%Y-%m-%d").date()
        query = query.where(Presence.date <= date_fin_obj)
    
    query = query.order_by(Presence.date.desc())
    result = await db.execute(query)
    
    return result.scalars().all()


# =============================================================================
# ===================== SALAIRES =====================
# =============================================================================

@router.get("/salaires/{chantier_id}")
async def calculer_salaires(
    chantier_id: int,
    date_debut: str,
    date_fin: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_salaires"))
):
    """
    Calculer les salaires des employés pour une période donnée
    
    ⚠️ SÉCURITÉ: Réservé aux rôles avec permission "view_salaires"
    - Admin Général
    - Comptable
    - Direction (lecture seule)
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    # Direction: vérifier lecture seule
    if role == RoleEnum.DIRECTION:
        # Peut voir mais pas exporter/modifier
        pass
    
    try:
        debut = datetime.strptime(date_debut, "%Y-%m-%d").date()
        fin = datetime.strptime(date_fin, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    # Récupérer les employés du chantier
    result = await db.execute(
        select(Employe).where(
            Employe.chantier_id == chantier_id,
            Employe.is_active == True
        ).order_by(Employe.nom)
    )
    employes = result.scalars().all()
    
    salaires = []
    total_general = 0
    
    for emp in employes:
        # Compter les jours présents
        pres_result = await db.execute(
            select(Presence).where(
                Presence.employe_id == emp.id,
                Presence.date >= debut,
                Presence.date <= fin,
                Presence.status == "present"
            )
        )
        presences = pres_result.scalars().all()
        
        jours_travailles = len(presences)
        heures_totales = sum(p.heures_travaillees for p in presences)
        salaire_periode = jours_travailles * (emp.salaire_journalier or 0)
        total_general += salaire_periode
        
        salaires.append({
            "employe_id": emp.id,
            "matricule": emp.matricule,
            "nom": emp.nom,
            "prenom": emp.prenom,
            "poste": emp.poste,
            "salaire_journalier": emp.salaire_journalier,
            "jours_travailles": jours_travailles,
            "heures_totales": heures_totales,
            "salaire_periode": salaire_periode
        })
    
    return {
        "chantier_id": chantier_id,
        "periode": {
            "debut": date_debut,
            "fin": date_fin
        },
        "employes": salaires,
        "total_general": total_general,
        "nombre_employes": len(salaires),
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": user.get("email")
    }


# =============================================================================
# STATISTIQUES EMPLOYÉS
# =============================================================================

@router.get("/stats/")
async def get_employes_stats(
    chantier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("view_employes"))
):
    """
    Statistiques des employés
    """
    role = user.get("role", RoleEnum.OUVRIER)
    
    query = select(Employe).where(Employe.is_active == True)
    
    if chantier_id:
        if not has_chantier_access(user, chantier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à ce chantier"
            )
        query = query.where(Employe.chantier_id == chantier_id)
    
    result = await db.execute(query)
    employes = result.scalars().all()
    
    # Stats par poste
    par_poste = {}
    for emp in employes:
        poste = emp.poste or "Non défini"
        if poste not in par_poste:
            par_poste[poste] = 0
        par_poste[poste] += 1
    
    stats = {
        "total_employes": len(employes),
        "par_poste": par_poste,
        "affectes": len([e for e in employes if e.chantier_id]),
        "non_affectes": len([e for e in employes if not e.chantier_id])
    }
    
    # Ajouter masse salariale si autorisé
    if has_permission(role, "view_salaires"):
        stats["masse_salariale_jour"] = sum(e.salaire_journalier or 0 for e in employes)
    
    return stats