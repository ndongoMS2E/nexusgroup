#!/bin/bash

API="http://localhost:8000/api/v1"

echo "🚀 Création des utilisateurs et données NEXUS GROUP"
echo "===================================================="

# 1. Admin
echo ""
echo "👤 Création ADMIN..."
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@nexusgroup.sn",
    "password": "Admin123!",
    "first_name": "Amadou",
    "last_name": "DIALLO",
    "phone": "+221771234567",
    "role": "admin"
  }' > /dev/null && echo "✅ Admin créé"

# 2. Comptable
echo ""
echo "💼 Création COMPTABLE..."
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "compta@nexusgroup.sn",
    "password": "Compta123!",
    "first_name": "Fatou",
    "last_name": "SARR",
    "phone": "+221779876543",
    "role": "comptable"
  }' > /dev/null && echo "✅ Comptable créé"

# Connexion admin pour créer les données
echo ""
echo "🔐 Connexion admin..."
TOKEN=$(curl -s -X POST "$API/auth/login" \
  -d "username=admin@nexusgroup.sn&password=Admin123!" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Créer les chantiers d'abord
echo ""
echo "🏗️ Création des chantiers..."

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Villa Almadies Premium",
    "adresse": "Rue 10, Almadies",
    "ville": "Dakar",
    "client_nom": "M. Abdoulaye Diop",
    "client_telephone": "+221771112233",
    "budget_prevu": 75000000
  }' > /dev/null && echo "✅ Chantier 1: Villa Almadies"

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Immeuble R+4 Ouest Foire",
    "adresse": "Avenue Bourguiba",
    "ville": "Dakar",
    "client_nom": "Mme Fatou Sarr",
    "budget_prevu": 150000000
  }' > /dev/null && echo "✅ Chantier 2: Immeuble Ouest Foire"

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Centre Commercial Plateau",
    "adresse": "Place de Indépendance",
    "ville": "Dakar",
    "client_nom": "SCI Plateau Invest",
    "budget_prevu": 250000000
  }' > /dev/null && echo "✅ Chantier 3: Centre Commercial"

# 3. Chef de chantier 1 (Villa Almadies)
echo ""
echo "👷 Création CHEF CHANTIER 1..."
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chef1@nexusgroup.sn",
    "password": "Chef123!",
    "first_name": "Mamadou",
    "last_name": "FALL",
    "phone": "+221775551122",
    "role": "chef_chantier",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Chef chantier 1 créé (Villa Almadies)"

# 4. Chef de chantier 2 (Immeuble)
echo ""
echo "👷 Création CHEF CHANTIER 2..."
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "chef2@nexusgroup.sn",
    "password": "Chef123!",
    "first_name": "Ousmane",
    "last_name": "NDIAYE",
    "phone": "+221776662233",
    "role": "chef_chantier",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Chef chantier 2 créé (Immeuble)"

# Créer les employés
echo ""
echo "👷 Création des employés..."

for i in 1 2 3 4 5; do
  curl -s -X POST "$API/employes/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"nom\": \"EMPLOYE$i\",
      \"prenom\": \"Ouvrier\",
      \"poste\": \"macon\",
      \"salaire_journalier\": 10000,
      \"date_embauche\": \"2025-01-0$i\",
      \"chantier_id\": 1
    }" > /dev/null
done
echo "✅ 5 employés créés pour chantier 1"

for i in 1 2 3; do
  curl -s -X POST "$API/employes/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"nom\": \"WORKER$i\",
      \"prenom\": \"Builder\",
      \"poste\": \"ferrailleur\",
      \"salaire_journalier\": 12000,
      \"date_embauche\": \"2025-02-0$i\",
      \"chantier_id\": 2
    }" > /dev/null
done
echo "✅ 3 employés créés pour chantier 2"

# Créer les dépenses
echo ""
echo "💰 Création des dépenses..."

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"libelle": "Ciment 200 sacs", "categorie": "materiel", "montant": 1500000, "date_depense": "2025-12-20", "fournisseur": "Ciments du Sahel", "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"libelle": "Fer à béton 100 barres", "categorie": "materiel", "montant": 900000, "date_depense": "2025-12-21", "fournisseur": "Touba Steel", "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"libelle": "Main oeuvre semaine", "categorie": "main_oeuvre", "montant": 500000, "date_depense": "2025-12-22", "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"libelle": "Gravier 20m3", "categorie": "materiel", "montant": 500000, "date_depense": "2025-12-23", "chantier_id": 2}' > /dev/null

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"libelle": "Transport matériaux", "categorie": "transport", "montant": 150000, "date_depense": "2025-12-24", "chantier_id": 2}' > /dev/null

echo "✅ 5 dépenses créées"

# Créer les matériels
echo ""
echo "📦 Création des matériels..."

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom": "Ciment CEM II", "categorie": "ciment", "unite": "sac", "quantite": 150, "seuil_alerte": 30, "prix_unitaire": 7500, "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom": "Fer 12mm", "categorie": "fer", "unite": "barre", "quantite": 80, "seuil_alerte": 20, "prix_unitaire": 9000, "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom": "Fer 8mm", "categorie": "fer", "unite": "barre", "quantite": 10, "seuil_alerte": 25, "prix_unitaire": 6000, "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom": "Sable", "categorie": "agregat", "unite": "m3", "quantite": 3, "seuil_alerte": 8, "prix_unitaire": 18000, "chantier_id": 1}' > /dev/null

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom": "Parpaings", "categorie": "autres", "unite": "piece", "quantite": 500, "seuil_alerte": 100, "prix_unitaire": 350, "chantier_id": 2}' > /dev/null

echo "✅ 5 matériels créés (2 en alerte)"

# Créer des notifications
curl -s -X POST "$API/notifications/check-stock/" -H "Authorization: Bearer $TOKEN" > /dev/null
echo "✅ Notifications créées"

echo ""
echo "===================================================="
echo "✅ TOUTES LES DONNÉES CRÉÉES AVEC SUCCÈS"
echo "===================================================="
echo ""
echo "📋 COMPTES UTILISATEURS:"
echo ""
echo "┌─────────────────┬──────────────────────┬─────────────┬─────────────────────────┐"
echo "│ Rôle            │ Email                │ Mot de passe│ Permissions             │"
echo "├─────────────────┼──────────────────────┼─────────────┼─────────────────────────┤"
echo "│ 👑 Admin        │ admin@nexusgroup.sn  │ Admin123!   │ Accès total             │"
echo "├─────────────────┼──────────────────────┼─────────────┼─────────────────────────┤"
echo "│ 💼 Comptable    │ compta@nexusgroup.sn │ Compta123!  │ Dépenses, Rapports,     │"
echo "│                 │                      │             │ Approbations            │"
echo "├─────────────────┼──────────────────────┼─────────────┼─────────────────────────┤"
echo "│ 👷 Chef Chant.1 │ chef1@nexusgroup.sn  │ Chef123!    │ Villa Almadies:         │"
echo "│                 │                      │             │ Pointage, Stock, Dép.   │"
echo "├─────────────────┼──────────────────────┼─────────────┼─────────────────────────┤"
echo "│ 👷 Chef Chant.2 │ chef2@nexusgroup.sn  │ Chef123!    │ Immeuble:               │"
echo "│                 │                      │             │ Pointage, Stock, Dép.   │"
echo "└─────────────────┴──────────────────────┴─────────────┴─────────────────────────┘"
echo ""
echo "🌐 Ouvrez: http://localhost:3000"
echo ""
