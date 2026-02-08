#!/bin/bash

API_URL="http://localhost:8000"
EMAIL=${1:-"admin@nexusgroup.sn"}
PASSWORD=${2:-"Admin123!"}

TOKEN=$(curl -s -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    export TOKEN
    echo "✅ Connexion réussie!"
    echo ""
    echo "Token sauvegardé dans \$TOKEN"
    echo ""
    echo "Exemple d'utilisation:"
    echo "curl -H \"Authorization: Bearer \$TOKEN\" $API_URL/api/v1/chantiers"
else
    echo "❌ Erreur de connexion"
fi
