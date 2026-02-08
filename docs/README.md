# NEXUS BUILDING SOLUTION

## 📋 Description

Application de gestion de chantiers pour entreprises de construction. Permet de gérer les chantiers, employés, dépenses, matériels, pointage et documents avec un système de rôles et permissions granulaire.

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRAEFIK (Reverse Proxy)                   │
│                    Port 80/443                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   FRONTEND          │       │   BACKEND           │
│   Angular 18        │       │   FastAPI           │
│   nginx             │       │   Python 3.11       │
│   /                 │       │   /api              │
└─────────────────────┘       └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   PostgreSQL 16     │
                              │   Base de données   │
                              └─────────────────────┘
```

## 🛠️ Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Frontend | Angular | 18.x |
| Backend | FastAPI | 0.100+ |
| Base de données | PostgreSQL | 16 |
| Reverse Proxy | Traefik | Latest |
| Conteneurisation | Docker | 29.x |
| OS Serveur | Ubuntu | 24.04 |

## 📁 Structure du Projet
```
~/apps/nexusgroup/
├── docker-compose.yml          # Orchestration des services
├── docs/                       # Documentation
│   ├── README.md              # Ce fichier
│   ├── ROLES.md               # Documentation des rôles
│   ├── API.md                 # Documentation API
│   └── DEPLOYMENT.md          # Guide de déploiement
├── nexus-frontend/            # Application Angular
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/          # Services, guards, interceptors
│   │   │   ├── shared/        # Composants partagés
│   │   │   └── features/      # Modules fonctionnels
│   │   └── environments/
│   ├── Dockerfile
│   └── nginx.conf
└── nexus-backend/             # API FastAPI
    ├── app/
    │   ├── api/v1/endpoints/  # Endpoints REST
    │   ├── core/              # Config, sécurité, permissions
    │   ├── models/            # Modèles SQLAlchemy
    │   └── schemas/           # Schémas Pydantic
    ├── Dockerfile
    └── requirements.txt
```

## 🚀 Déploiement

### Prérequis

- VPS Ubuntu 24.04
- Docker installé
- Domaine configuré (optionnel)

### Installation rapide
```bash
# Cloner les repositories
git clone https://github.com/ndongoMS2E/nexus-frontend.git
git clone https://github.com/ndongoMS2E/nexus-backend.git

# Lancer l'application
cd ~/apps/nexusgroup
docker compose up -d

# Créer l'admin initial
docker exec -it nexus-postgres psql -U nexus -d nexusgroup
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| DB_HOST | Hôte PostgreSQL | nexus-postgres |
| DB_USER | Utilisateur DB | nexus |
| DB_PASSWORD | Mot de passe DB | nexus2026 |
| DB_NAME | Nom de la base | nexusgroup |
| SECRET_KEY | Clé JWT | (à définir) |

## 🔐 Sécurité

- **Authentification** : JWT avec refresh token
- **Autorisation** : RBAC (8 rôles)
- **HTTPS** : Let's Encrypt via Traefik
- **Firewall** : UFW activé (22, 80, 443)
- **SSH** : Authentification par clé uniquement
- **Fail2ban** : Protection brute-force

## 📊 Fonctionnalités

### Modules

| Module | Description |
|--------|-------------|
| Dashboard | Vue d'ensemble, statistiques |
| Chantiers | Gestion des projets de construction |
| Dépenses | Suivi budgétaire et financier |
| Employés | Gestion du personnel |
| Pointage | Présences et heures travaillées |
| Matériels | Stock et équipements |
| Documents | GED (photos, plans, factures) |
| Notifications | Alertes et rappels |
| Utilisateurs | Gestion des comptes (admin) |

## 👥 Équipe

- **Développeur** : Ndongo
- **Entreprise** : NEXUS BUILDING SOLUTION

## 📄 Licence

Propriétaire - © 2026 NEXUS BUILDING SOLUTION
