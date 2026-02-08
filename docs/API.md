# Documentation API

## Base URL
```
https://votre-domaine.com/api/v1
```

## Authentification

L'API utilise JWT (JSON Web Token). Incluez le token dans le header :
```
Authorization: Bearer <votre_token>
```

### Obtenir un token
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=email@exemple.com&password=motdepasse
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Rafraîchir le token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## Endpoints

### 🔐 Auth

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| POST | `/auth/login` | Connexion | Public |
| POST | `/auth/register` | Créer utilisateur | `admin_general` |
| POST | `/auth/refresh` | Rafraîchir token | Authentifié |
| GET | `/auth/me` | Profil courant | Authentifié |
| GET | `/auth/me/permissions` | Mes permissions | Authentifié |
| GET | `/auth/users` | Liste utilisateurs | `view_all_employes` |
| GET | `/auth/roles` | Liste des rôles | Authentifié |
| PUT | `/auth/users/{id}/role` | Modifier rôle | `admin_general` |
| PUT | `/auth/users/{id}/activate` | Activer compte | `admin_general` |
| PUT | `/auth/users/{id}/deactivate` | Désactiver compte | `admin_general` |
| PUT | `/auth/change-password` | Changer mot de passe | Authentifié |

---

### 🏗️ Chantiers

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/chantiers/` | Liste des chantiers | `view_chantiers` |
| POST | `/chantiers/` | Créer un chantier | `admin_general` |
| GET | `/chantiers/{id}` | Détail chantier | `view_chantiers` |
| PUT | `/chantiers/{id}` | Modifier chantier | `edit_chantier` |
| DELETE | `/chantiers/{id}` | Supprimer chantier | `admin_general` |
| PUT | `/chantiers/{id}/status` | Changer statut | `admin_general` |
| GET | `/chantiers/{id}/stats` | Statistiques | `view_chantiers` |

**Exemple - Créer un chantier :**
```http
POST /chantiers/
Authorization: Bearer <token>
Content-Type: application/json

{
  "nom": "Résidence Les Almadies",
  "description": "Construction immeuble R+5",
  "adresse": "Dakar, Almadies",
  "client_nom": "M. Diallo",
  "client_telephone": "+221771234567",
  "date_debut": "2026-03-01",
  "date_fin_prevue": "2026-12-31",
  "budget_prevu": 150000000,
  "status": "en_cours"
}
```

---

### 💰 Dépenses

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/depenses/` | Liste dépenses | `view_depenses` |
| POST | `/depenses/` | Créer dépense | `create_depense` |
| GET | `/depenses/{id}` | Détail dépense | `view_depenses` |
| PUT | `/depenses/{id}` | Modifier dépense | `create_depense` |
| DELETE | `/depenses/{id}` | Supprimer | `admin_general` |
| PUT | `/depenses/{id}/approve` | Approuver | `admin_general` |
| PUT | `/depenses/{id}/reject` | Rejeter | `admin_general` |
| GET | `/depenses/stats` | Statistiques | `view_depenses` |

**Statuts de dépense :**
- `en_attente` : En attente de validation
- `approuvee` : Validée par admin
- `rejetee` : Rejetée
- `payee` : Payée

---

### 👷 Employés

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/employes/` | Liste employés | `view_employes` |
| POST | `/employes/` | Créer employé | `admin_general` |
| GET | `/employes/{id}` | Détail employé | `view_employes` |
| PUT | `/employes/{id}` | Modifier | `admin_general` |
| DELETE | `/employes/{id}` | Supprimer | `admin_general` |
| GET | `/employes/{id}/presences` | Historique présences | `view_presences` |

---

### 📋 Pointage / Présences

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/presences/` | Liste présences | `view_presences` |
| POST | `/presences/` | Créer présence | `create_presence` |
| POST | `/presences/pointer` | Pointer (entrée/sortie) | `pointer` |
| GET | `/presences/today` | Présences du jour | `view_presences` |
| GET | `/presences/stats` | Statistiques | `view_presences` |

**Exemple - Pointer :**
```http
POST /presences/pointer
Authorization: Bearer <token>
Content-Type: application/json

{
  "employe_id": 5,
  "chantier_id": 1,
  "type": "entree"
}
```

---

### 📦 Matériels / Stock

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/materiels/` | Liste matériels | `view_stock` |
| POST | `/materiels/` | Créer matériel | `create_stock` |
| GET | `/materiels/{id}` | Détail | `view_stock` |
| PUT | `/materiels/{id}` | Modifier | `edit_stock` |
| DELETE | `/materiels/{id}` | Supprimer | `admin_general` |
| POST | `/materiels/mouvement` | Entrée/Sortie stock | `mouvement_stock` |
| POST | `/materiels/reception` | Réception livraison | `receive_materiel` |
| GET | `/materiels/alertes` | Alertes stock bas | `view_stock` |

**Types de mouvement :**
- `entree` : Entrée en stock
- `sortie` : Sortie du stock
- `transfert` : Transfert entre chantiers

---

### 📁 Documents

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/documents/` | Liste documents | `view_documents` |
| POST | `/documents/` | Upload document | `upload_document` |
| GET | `/documents/{id}` | Détail | `view_documents` |
| GET | `/documents/{id}/download` | Télécharger | `download_document` |
| DELETE | `/documents/{id}` | Supprimer | `delete_document` |
| PUT | `/documents/{id}/validate` | Valider pour client | `validate_document_client` |

**Types de document :**
- `photo` : Photo de chantier
- `plan` : Plan technique
- `facture` : Facture
- `bon_livraison` : Bon de livraison
- `contrat` : Contrat
- `rapport` : Rapport

---

### 🔔 Notifications

| Méthode | Endpoint | Description | Permission |
|---------|----------|-------------|------------|
| GET | `/notifications/` | Mes notifications | `view_notifications` |
| GET | `/notifications/count` | Nombre non lues | `view_notifications` |
| PUT | `/notifications/{id}/read` | Marquer comme lue | `view_notifications` |
| PUT | `/notifications/read-all` | Tout marquer lu | `view_notifications` |

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Permission refusée |
| 404 | Ressource non trouvée |
| 422 | Erreur de validation |
| 500 | Erreur serveur |

**Format d'erreur :**
```json
{
  "detail": "Message d'erreur explicatif"
}
```

---

## Pagination

Les endpoints de liste supportent la pagination :
```http
GET /chantiers/?skip=0&limit=20
```

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| skip | Nombre d'éléments à ignorer | 0 |
| limit | Nombre max d'éléments | 20 |

---

## Filtres

Certains endpoints supportent des filtres :
```http
GET /depenses/?chantier_id=1&status=en_attente
GET /employes/?chantier_id=1&poste=maçon
GET /presences/?date=2026-02-08&chantier_id=1
```

---

## Documentation Interactive

Swagger UI disponible à :
```
https://votre-domaine.com/api/docs
```

ReDoc disponible à :
```
https://votre-domaine.com/api/redoc
```
