# NEXUS GROUP - Frontend Angular

Application Angular de gestion de chantier pour NEXUS GROUP.

## 🚀 Démarrage rapide

### Prérequis
- Node.js 18+
- npm ou yarn
- Backend FastAPI en cours d'exécution sur `http://localhost:8000`

### Installation

```bash
cd nexus-frontend

# Installer les dépendances
npm install

# Lancer en mode développement
ng serve
# ou
npm start
```

L'application sera accessible sur **http://localhost:4200**

### Build production

```bash
ng build --configuration=production
```

Les fichiers seront générés dans `dist/nexus-frontend/`

## 📁 Structure du projet

```
src/
├── app/
│   ├── core/                    # Services, guards, interceptors
│   │   ├── guards/
│   │   ├── interceptors/
│   │   ├── models/              # Interfaces TypeScript
│   │   └── services/            # Services API
│   ├── features/                # Modules fonctionnels
│   │   ├── auth/                # Login
│   │   ├── dashboard/           # Tableau de bord
│   │   ├── chantiers/           # Gestion des chantiers
│   │   ├── depenses/            # Gestion des dépenses
│   │   ├── employes/            # Gestion des employés
│   │   ├── pointage/            # Pointage journalier
│   │   ├── materiels/           # Gestion des matériels/stock
│   │   ├── documents/           # Gestion documentaire
│   │   └── notifications/       # Centre de notifications
│   └── shared/                  # Composants partagés
│       ├── components/
│       │   ├── layout/          # Layout principal
│       │   ├── sidebar/         # Barre latérale
│       │   └── modal/           # Modal réutilisable
│       └── pipes/               # Pipes (money, etc.)
├── environments/                # Configuration environnement
└── styles/                      # Styles SCSS globaux
```

## 🎨 Design

- **Thème** : Dark mode avec dégradés gris/blanc
- **Couleurs principales** :
  - Background : `#0a0a0a` - `#1a1a1a` - `#252525`
  - Texte : `#fff` - `#888` - `#666`
  - Success : `#4caf50`
  - Warning : `#ff9800`
  - Danger : `#f44336`
  - Info : `#2196f3`

## 📋 Fonctionnalités

- **Authentification** : Login JWT avec guard de route
- **Dashboard** : Statistiques et chantiers récents
- **Chantiers** : CRUD complet + export PDF
- **Dépenses** : CRUD + approbation
- **Employés** : CRUD complet
- **Pointage** : Pointage journalier par chantier
- **Matériels** : Gestion stock + mouvements + alertes
- **Documents** : Upload/download de fichiers
- **Notifications** : Liste + marquer comme lu

## ⚙️ Configuration API

Modifier `src/environments/environment.ts` :

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1'
};
```

## 📄 Licence

Propriétaire - NEXUS GROUP
