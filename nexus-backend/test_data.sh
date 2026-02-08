#!/bin/bash

API="http://localhost:8000/api/v1"

echo "🚀 Création des données de test NEXUS GROUP"
echo "============================================"

# 1. Créer l'utilisateur admin
echo ""
echo "👤 Création utilisateur admin..."
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@nexusgroup.sn",
    "password": "Admin123!",
    "first_name": "Amadou",
    "last_name": "DIALLO",
    "phone": "+221771234567",
    "role": "admin"
  }' | python3 -m json.tool 2>/dev/null || echo "Admin existe déjà"

# 2. Se connecter
echo ""
echo "🔐 Connexion..."
TOKEN=$(curl -s -X POST "$API/auth/login" \
  -d "username=admin@nexusgroup.sn&password=Admin123!" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token obtenu: ${TOKEN:0:50}..."

# 3. Créer les chantiers
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
    "budget_prevu": 75000000,
    "description": "Villa de luxe 5 chambres avec piscine"
  }' > /dev/null && echo "✅ Chantier 1: Villa Almadies"

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Immeuble R+4 Ouest Foire",
    "adresse": "Avenue Bourguiba, Lot 45",
    "ville": "Dakar",
    "client_nom": "Mme Fatou Sarr",
    "client_telephone": "+221779998877",
    "budget_prevu": 150000000,
    "description": "Immeuble résidentiel 12 appartements"
  }' > /dev/null && echo "✅ Chantier 2: Immeuble Ouest Foire"

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Centre Commercial Plateau",
    "adresse": "Place de Indépendance",
    "ville": "Dakar",
    "client_nom": "SCI Plateau Invest",
    "client_telephone": "+221338891122",
    "budget_prevu": 250000000,
    "description": "Centre commercial 3 niveaux"
  }' > /dev/null && echo "✅ Chantier 3: Centre Commercial"

curl -s -X POST "$API/chantiers/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Résidence Saly Beach",
    "adresse": "Route de Ngaparou",
    "ville": "Saly",
    "client_nom": "M. Pierre Durand",
    "client_telephone": "+221776543210",
    "budget_prevu": 95000000,
    "description": "Villa bord de mer avec 4 chambres"
  }' > /dev/null && echo "✅ Chantier 4: Résidence Saly"

# 4. Créer les employés
echo ""
echo "👷 Création des employés..."

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "DIALLO",
    "prenom": "Mamadou",
    "telephone": "+221771112233",
    "poste": "chef_equipe",
    "salaire_journalier": 15000,
    "date_embauche": "2024-01-15",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Employé 1: Mamadou DIALLO (Chef équipe)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "NDIAYE",
    "prenom": "Ousmane",
    "telephone": "+221772223344",
    "poste": "macon",
    "salaire_journalier": 10000,
    "date_embauche": "2024-02-01",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Employé 2: Ousmane NDIAYE (Maçon)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "SOW",
    "prenom": "Ibrahima",
    "telephone": "+221773334455",
    "poste": "ferrailleur",
    "salaire_journalier": 12000,
    "date_embauche": "2024-02-10",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Employé 3: Ibrahima SOW (Ferrailleur)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "FALL",
    "prenom": "Cheikh",
    "telephone": "+221774445566",
    "poste": "manoeuvre",
    "salaire_journalier": 5000,
    "date_embauche": "2024-03-01",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Employé 4: Cheikh FALL (Manoeuvre)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "GUEYE",
    "prenom": "Modou",
    "telephone": "+221775556677",
    "poste": "electricien",
    "salaire_journalier": 12000,
    "date_embauche": "2024-03-15",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Employé 5: Modou GUEYE (Électricien)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "BA",
    "prenom": "Aliou",
    "telephone": "+221776667788",
    "poste": "plombier",
    "salaire_journalier": 11000,
    "date_embauche": "2024-04-01",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Employé 6: Aliou BA (Plombier)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "MBAYE",
    "prenom": "Serigne",
    "telephone": "+221777778899",
    "poste": "macon",
    "salaire_journalier": 10000,
    "date_embauche": "2024-04-15",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Employé 7: Serigne MBAYE (Maçon)"

curl -s -X POST "$API/employes/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "DIOP",
    "prenom": "Pape",
    "telephone": "+221778889900",
    "poste": "chef_equipe",
    "salaire_journalier": 15000,
    "date_embauche": "2024-05-01",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Employé 8: Pape DIOP (Chef équipe)"

# 5. Créer les dépenses
echo ""
echo "💰 Création des dépenses..."

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Achat ciment CEM II - 200 sacs",
    "categorie": "materiel",
    "montant": 1500000,
    "date_depense": "2025-12-20",
    "fournisseur": "Ciments du Sahel",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Dépense 1: Ciment (1,500,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Fer à béton 12mm - 100 barres",
    "categorie": "materiel",
    "montant": 900000,
    "date_depense": "2025-12-21",
    "fournisseur": "Touba Steel",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Dépense 2: Fer à béton (900,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Main oeuvre semaine 51",
    "categorie": "main_oeuvre",
    "montant": 450000,
    "date_depense": "2025-12-22",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Dépense 3: Main d'oeuvre (450,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Location bétonnière - 1 mois",
    "categorie": "location",
    "montant": 250000,
    "date_depense": "2025-12-15",
    "fournisseur": "Locmat Sénégal",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Dépense 4: Location bétonnière (250,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Transport matériaux",
    "categorie": "transport",
    "montant": 150000,
    "date_depense": "2025-12-23",
    "fournisseur": "Trans Diallo",
    "chantier_id": 1
  }' > /dev/null && echo "✅ Dépense 5: Transport (150,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Gravier 15/25 - 20m3",
    "categorie": "materiel",
    "montant": 500000,
    "date_depense": "2025-12-24",
    "fournisseur": "Carrières de Diack",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Dépense 6: Gravier (500,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Câbles électriques",
    "categorie": "materiel",
    "montant": 320000,
    "date_depense": "2025-12-25",
    "fournisseur": "Elec Pro Dakar",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Dépense 7: Câbles (320,000 FCFA)"

curl -s -X POST "$API/depenses/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "libelle": "Tuyaux PVC plomberie",
    "categorie": "materiel",
    "montant": 180000,
    "date_depense": "2025-12-26",
    "fournisseur": "Plomba Services",
    "chantier_id": 2
  }' > /dev/null && echo "✅ Dépense 8: Tuyaux PVC (180,000 FCFA)"

# 6. Créer les matériels
echo ""
echo "📦 Création des matériels en stock..."

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Ciment CEM II 42.5",
    "categorie": "ciment",
    "unite": "sac",
    "quantite": 150,
    "seuil_alerte": 30,
    "prix_unitaire": 7500,
    "chantier_id": 1
  }' > /dev/null && echo "✅ Matériel 1: Ciment (150 sacs)"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Fer à béton 12mm",
    "categorie": "fer",
    "unite": "barre",
    "quantite": 80,
    "seuil_alerte": 20,
    "prix_unitaire": 9000,
    "chantier_id": 1
  }' > /dev/null && echo "✅ Matériel 2: Fer 12mm (80 barres)"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Fer à béton 8mm",
    "categorie": "fer",
    "unite": "barre",
    "quantite": 15,
    "seuil_alerte": 25,
    "prix_unitaire": 6000,
    "chantier_id": 1
  }' > /dev/null && echo "✅ Matériel 3: Fer 8mm (15 barres) ⚠️ ALERTE"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Gravier 15/25",
    "categorie": "agregat",
    "unite": "m3",
    "quantite": 12,
    "seuil_alerte": 5,
    "prix_unitaire": 25000,
    "chantier_id": 1
  }' > /dev/null && echo "✅ Matériel 4: Gravier (12 m³)"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Sable fin",
    "categorie": "agregat",
    "unite": "m3",
    "quantite": 3,
    "seuil_alerte": 8,
    "prix_unitaire": 18000,
    "chantier_id": 1
  }' > /dev/null && echo "✅ Matériel 5: Sable (3 m³) ⚠️ ALERTE"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Parpaings 15x20x40",
    "categorie": "autres",
    "unite": "piece",
    "quantite": 500,
    "seuil_alerte": 100,
    "prix_unitaire": 350,
    "chantier_id": 2
  }' > /dev/null && echo "✅ Matériel 6: Parpaings (500 pièces)"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Câble électrique 2.5mm",
    "categorie": "electricite",
    "unite": "m",
    "quantite": 200,
    "seuil_alerte": 50,
    "prix_unitaire": 800,
    "chantier_id": 2
  }' > /dev/null && echo "✅ Matériel 7: Câble élec (200 m)"

curl -s -X POST "$API/materiels/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Tuyau PVC 100mm",
    "categorie": "plomberie",
    "unite": "barre",
    "quantite": 8,
    "seuil_alerte": 10,
    "prix_unitaire": 12000,
    "chantier_id": 2
  }' > /dev/null && echo "✅ Matériel 8: Tuyau PVC (8 barres) ⚠️ ALERTE"

# 7. Créer des présences
echo ""
echo "📋 Création des pointages..."

TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)

curl -s -X POST "$API/employes/presences/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"employe_id\": 1,
    \"chantier_id\": 1,
    \"date\": \"$YESTERDAY\",
    \"heures_travaillees\": 8,
    \"status\": \"present\"
  }" > /dev/null && echo "✅ Pointage: Mamadou présent hier"

curl -s -X POST "$API/employes/presences/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"employe_id\": 2,
    \"chantier_id\": 1,
    \"date\": \"$YESTERDAY\",
    \"heures_travaillees\": 8,
    \"status\": \"present\"
  }" > /dev/null && echo "✅ Pointage: Ousmane présent hier"

curl -s -X POST "$API/employes/presences/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"employe_id\": 3,
    \"chantier_id\": 1,
    \"date\": \"$YESTERDAY\",
    \"heures_travaillees\": 0,
    \"status\": \"absent\"
  }" > /dev/null && echo "✅ Pointage: Ibrahima absent hier"

curl -s -X POST "$API/employes/presences/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"employe_id\": 4,
    \"chantier_id\": 1,
    \"date\": \"$YESTERDAY\",
    \"heures_travaillees\": 8,
    \"status\": \"present\"
  }" > /dev/null && echo "✅ Pointage: Cheikh présent hier"

# 8. Créer des notifications
echo ""
echo "🔔 Création des notifications..."

curl -s -X POST "$API/notifications/check-stock/" \
  -H "Authorization: Bearer $TOKEN" > /dev/null && echo "✅ Notifications stock créées"

# 9. Résumé
echo ""
echo "============================================"
echo "✅ DONNÉES DE TEST CRÉÉES AVEC SUCCÈS"
echo "============================================"
echo ""
echo "📊 Résumé:"
echo "   - 4 Chantiers"
echo "   - 8 Employés"
echo "   - 8 Dépenses"
echo "   - 8 Matériels (3 en alerte)"
echo "   - 4 Pointages"
echo "   - Notifications automatiques"
echo ""
echo "🔐 Connexion:"
echo "   Email: admin@nexusgroup.sn"
echo "   Mot de passe: Admin123!"
echo ""
echo "🌐 Ouvrez: http://localhost:3000"
echo ""
