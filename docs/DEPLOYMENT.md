# Guide de Déploiement

## Prérequis

- VPS Ubuntu 24.04 LTS
- Minimum 4GB RAM, 2 vCPU
- Docker et Docker Compose installés
- Domaine (optionnel)

## Installation

### 1. Connexion SSH
```bash
ssh user@votre-serveur
```

### 2. Installation Docker
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Structure des dossiers
```bash
mkdir -p ~/apps/{traefik,nexusgroup,data/postgres}
cd ~/apps/nexusgroup
```

### 4. Cloner les repositories
```bash
git clone https://github.com/ndongoMS2E/nexus-frontend.git
git clone https://github.com/ndongoMS2E/nexus-backend.git
```

### 5. Configuration Traefik

Créer `~/apps/traefik/traefik.yml` :
```yaml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: web

certificatesResolvers:
  letsencrypt:
    acme:
      email: votre-email@exemple.com
      storage: /acme.json
      httpChallenge:
        entryPoint: web
```

Créer `~/apps/traefik/docker-compose.yml` :
```yaml
networks:
  web:
    external: true

services:
  traefik:
    image: traefik:latest
    container_name: traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "127.0.0.1:8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./acme.json:/acme.json
    networks:
      - web
```
```bash
# Créer le réseau et les fichiers
docker network create web
touch ~/apps/traefik/acme.json
chmod 600 ~/apps/traefik/acme.json

# Lancer Traefik
cd ~/apps/traefik
docker compose up -d
```

### 6. Configuration NEXUS

Créer `~/apps/nexusgroup/docker-compose.yml` :
```yaml
networks:
  web:
    external: true
  internal:

services:
  nexus-backend:
    build: ./nexus-backend
    container_name: nexus-backend
    restart: unless-stopped
    environment:
      - DB_HOST=nexus-postgres
      - DB_USER=nexus
      - DB_PASSWORD=nexus2026
      - DB_NAME=nexusgroup
      - SECRET_KEY=votre-cle-secrete-tres-longue
    depends_on:
      - postgres
    networks:
      - web
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nexus-api.rule=Host(`votre-domaine.com`) && PathPrefix(`/api`)"
      - "traefik.http.routers.nexus-api.entrypoints=web"
      - "traefik.http.services.nexus-api.loadbalancer.server.port=8000"

  nexus-frontend:
    build: ./nexus-frontend
    container_name: nexus-frontend
    restart: unless-stopped
    depends_on:
      - nexus-backend
    networks:
      - web
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.nexus-front.rule=Host(`votre-domaine.com`)"
      - "traefik.http.routers.nexus-front.entrypoints=web"
      - "traefik.http.services.nexus-front.loadbalancer.server.port=80"

  postgres:
    image: postgres:16-alpine
    container_name: nexus-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=nexus
      - POSTGRES_PASSWORD=nexus2026
      - POSTGRES_DB=nexusgroup
    volumes:
      - ~/apps/data/postgres:/var/lib/postgresql/data
    networks:
      - internal
```

### 7. Lancement
```bash
cd ~/apps/nexusgroup
docker compose up -d --build
```

### 8. Initialisation de la base
```bash
# Créer l'admin initial
docker exec -it nexus-backend python -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=12)
print(pwd_context.hash('votre-mot-de-passe'))
"

# Copier le hash et l'utiliser
docker exec -it nexus-postgres psql -U nexus -d nexusgroup

INSERT INTO users (email, hashed_password, first_name, last_name, phone, role, is_active, created_at)
VALUES (
  'admin@votredomaine.com',
  'LE_HASH_GENERE',
  'Admin',
  'NEXUS',
  '+221770000000',
  'admin_general',
  true,
  NOW()
);

\q
```

## Sécurisation

### Firewall
```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2ban
```bash
sudo apt install fail2ban -y
sudo nano /etc/fail2ban/jail.local
```
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
maxretry = 3
```
```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### SSH par clé
```bash
# Sur votre machine locale
ssh-keygen -t ed25519
ssh-copy-id user@serveur

# Sur le serveur
sudo nano /etc/ssh/sshd_config
# Modifier :
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

sudo systemctl restart ssh
```

## Maintenance

### Logs
```bash
# Tous les logs
docker compose logs -f

# Un service spécifique
docker logs nexus-backend --tail 100
```

### Backup base de données
```bash
# Backup
docker exec nexus-postgres pg_dump -U nexus nexusgroup > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i nexus-postgres psql -U nexus nexusgroup < backup.sql
```

### Mise à jour
```bash
cd ~/apps/nexusgroup
git -C nexus-frontend pull
git -C nexus-backend pull
docker compose up -d --build
```

## Dépannage

### Container ne démarre pas
```bash
docker compose logs nom-service
docker compose down
docker compose up -d
```

### Erreur 502 Bad Gateway
```bash
# Vérifier que le backend est up
docker ps
docker logs nexus-backend

# Redémarrer
docker compose restart nexus-backend
```

### Base de données inaccessible
```bash
# Vérifier PostgreSQL
docker logs nexus-postgres

# Tester la connexion
docker exec -it nexus-postgres psql -U nexus -d nexusgroup -c "\dt"
```
