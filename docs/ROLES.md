# Système de Rôles et Permissions

## Vue d'ensemble

NEXUS BUILDING SOLUTION utilise un système RBAC (Role-Based Access Control) avec 8 rôles distincts.

## 📊 Matrice des accès par module

| Module | Admin Général | Admin Chantier | Comptable | Chef Chantier | Magasinier | Ouvrier | Client | Direction |
|--------|:-------------:|:--------------:|:---------:|:-------------:|:----------:|:-------:|:------:|:---------:|
| Dashboard | ✅ Complet | ✅ Chantiers | ✅ Finance | ✅ Terrain | ✅ Stock | ✅ Limité | ✅ Propre | ✅ Global |
| Chantiers | ✅ CRUD | ✅ Assignés | ❌ | ✅ Assignés | ❌ | ❌ | ✅ Propre | ✅ Lecture |
| Dépenses | ✅ CRUD | ❌ | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ✅ Lecture |
| Employés | ✅ CRUD | ✅ Lecture | ✅ Salaires | ✅ Lecture | ❌ | ❌ | ❌ | ✅ Lecture |
| Pointage | ✅ CRUD | ✅ Gestion | ✅ Lecture | ✅ Gestion | ❌ | ✅ Personnel | ❌ | ❌ |
| Matériels | ✅ CRUD | ✅ Validation | ❌ | ✅ Demandes | ✅ CRUD | ❌ | ❌ | ✅ Lecture |
| Documents | ✅ CRUD | ✅ CRUD | ✅ Lecture | ✅ Upload | ❌ | ❌ | ✅ Validés | ✅ Lecture |
| Utilisateurs | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 1. 👑 Administrateur Général

**Code** : `admin_general`  
**Niveau** : 100  
**Couleur** : 🔴 Rouge

### Accès
- ✅ **Accès total au système**
- ✅ Création / modification / suppression de tous les utilisateurs
- ✅ Accès à tous les chantiers
- ✅ Validation finale (dépenses, commandes, modifications, documents)
- ✅ Gestion des budgets globaux et par chantier
- ✅ Accès à tous les rapports (financiers, techniques, RH)
- ✅ Paramétrage du logiciel

### Restrictions
- ⛔ Aucune restriction

---

## 2. 🏗️ Administrateur de Chantier

**Code** : `admin_chantier`  
**Niveau** : 80  
**Couleur** : 🟠 Orange

### Accès
- ✅ Accès complet à un ou plusieurs chantiers assignés
- ✅ Validation des demandes de matériaux
- ✅ Validation des modifications proposées par le chef de chantier
- ✅ Consultation des budgets du chantier (sans modification globale)
- ✅ Accès aux documents et rapports du chantier

### Restrictions
- ⛔ Pas d'accès aux autres chantiers
- ⛔ Pas d'accès aux paramètres globaux
- ⛔ Pas de création d'utilisateurs

---

## 3. 💰 Comptable / Financier

**Code** : `comptable`  
**Niveau** : 70  
**Couleur** : 🟢 Vert

### Accès
- ✅ **Consultation** : Budget prévu/réel, dépenses par chantier/lot, prévisions
- ✅ **Gestion** : Paiements ouvriers, factures fournisseurs, avances et soldes
- ✅ **Export** : PDF, Excel
- ✅ Lecture seule des documents techniques

### Restrictions
- ⛔ Aucune modification technique
- ⛔ Aucun accès au planning ou aux tâches
- ⛔ Pas d'accès aux chantiers (menu)
- ⛔ Pas d'accès aux matériels

---

## 4. 👷 Chef de Chantier / Conducteur de Travaux

**Code** : `chef_chantier`  
**Niveau** : 60  
**Couleur** : 🔵 Bleu

### Accès
- ✅ **Création/MAJ** : Tâches, avancement (%), journal de chantier
- ✅ **Upload** : Photos, vidéos, documents
- ✅ Pointage des ouvriers
- ✅ Gestion du matériel affecté à son chantier
- ✅ Consultation du stock du chantier
- ✅ **Demandes** : Matériaux, équipements
- ✅ Proposition de modifications (validation Admin requise)

### Restrictions
- ⛔ Pas d'accès aux budgets globaux
- ⛔ Pas de validation financière
- ⛔ Pas d'accès au menu Dépenses

---

## 5. 📦 Magasinier / Gestionnaire de Stock

**Code** : `magasinier`  
**Niveau** : 50  
**Couleur** : 🩵 Cyan

### Accès
- ✅ **Gestion stock** : Entrées/sorties, quantités disponibles
- ✅ Affectation du matériel aux chantiers
- ✅ Réception des matériaux
- ✅ Historique des mouvements
- ✅ Validation logistique (pas financière)

### Restrictions
- ⛔ Pas d'accès aux budgets
- ⛔ Pas d'accès aux données RH
- ⛔ Pas d'accès aux chantiers, dépenses, employés, documents

---

## 6. 🔧 Ouvrier / Technicien

**Code** : `ouvrier`  
**Niveau** : 20  
**Couleur** : ⬜ Gris

### Accès
- ✅ **Consultation** : Tâches assignées
- ✅ Pointage personnel (entrée/sortie)

### Restrictions
- ⛔ Aucun accès aux documents sensibles
- ⛔ Aucun accès financier
- ⛔ Lecture + saisie minimale uniquement
- ⛔ Seuls Dashboard, Pointage, Notifications visibles

---

## 7. 🏠 Client

**Code** : `client`  
**Niveau** : 10  
**Couleur** : 🟣 Indigo

### Accès
- ✅ Accès à une page dédiée à **son** chantier
- ✅ **Visualisation** : Avancement global, photos/vidéos/documents validés
- ✅ Commentaires et avis
- ✅ Historique des étapes importantes

### Restrictions
- ⛔ Aucun accès aux budgets internes
- ⛔ Aucun accès RH
- ⛔ Aucun accès aux documents non validés
- ⛔ Seuls Dashboard, Chantiers (propre), Documents (validés), Notifications

---

## 8. 📊 Direction / Associé

**Code** : `direction`  
**Niveau** : 90  
**Couleur** : 🟣 Violet

### Accès
- ✅ **Lecture seule** sur :
  - Tous les chantiers
  - Budgets
  - Rapports
  - Dashboard global

### Restrictions
- ⛔ **AUCUNE modification possible**
- ⛔ Pas d'accès au Pointage ni aux Utilisateurs

---

## 🔒 Règles de sécurité globales

1. **Validation Admin** : Toute modification sensible (budget, stock, données clés) nécessite validation Admin
2. **Audit** : Historique des actions (qui a fait quoi, quand)
3. **Permissions par chantier** : Accès configurable par chantier
4. **Mobile sécurisé** : Accès mobile avec mêmes restrictions

---

## 🛡️ Actions nécessitant validation Admin

| Action | Rôles pouvant proposer | Validateur |
|--------|------------------------|------------|
| Approbation dépense | Comptable, Chef chantier | Admin Général |
| Validation commande finale | Admin chantier | Admin Général |
| Modification budget global | - | Admin Général |
| Suppression employé | - | Admin Général |
| Changement de rôle | - | Admin Général |
| Document visible client | Admin chantier, Chef chantier | Admin Général |
