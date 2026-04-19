#!/usr/bin/env bash
# Build + push les images Docker Hub + deploiement automatique sur le VPS
# Usage: ./deploy.sh v1.1.2
# Usage: ./deploy.sh v1.1.2 --no-deploy   (build + push seulement, sans toucher au VPS)

set -euo pipefail

VERSION="${1:-}"
MODE="${2:-}"

if [[ -z "$VERSION" ]]; then
  echo "❌ Usage: ./deploy.sh <version>  (ex: v1.1.2)"
  echo "   Ou: ./deploy.sh <version> --no-deploy  (push seulement, pas de deploy VPS)"
  exit 1
fi

if ! [[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Format version invalide. Attendu: vX.Y.Z (ex: v1.1.2)"
  exit 1
fi

DOCKER_USER="sokevinjonas"
SERVICES=("backend" "frontend")

# ── Config VPS ──
VPS_HOST="admin@72.61.98.7"
VPS_PATH="/home/admin/projects/habileo"
HEALTHCHECK_URL="https://api-habileo.couturart.app/api/health"

# ─── Step 1 : Build ────────────────────────────────────────
echo ""
echo "🔨 Build des images habileo..."
docker compose build

# ─── Step 2 : Tag ──────────────────────────────────────────
echo ""
echo "🏷️  Tag $VERSION + latest..."
for svc in "${SERVICES[@]}"; do
  docker tag "habileo-$svc:latest" "$DOCKER_USER/habileo-$svc:$VERSION"
  docker tag "habileo-$svc:latest" "$DOCKER_USER/habileo-$svc:latest"
  echo "   ✓ habileo-$svc → $DOCKER_USER/habileo-$svc:$VERSION"
done

# ─── Step 3 : Push ─────────────────────────────────────────
echo ""
echo "📤 Push vers Docker Hub..."
for svc in "${SERVICES[@]}"; do
  docker push "$DOCKER_USER/habileo-$svc:$VERSION"
  docker push "$DOCKER_USER/habileo-$svc:latest"
done

echo ""
echo "✅ Images publiees sur Docker Hub ($VERSION + latest)"

# ─── Step 4 : Deploy sur le VPS ────────────────────────────
if [[ "$MODE" == "--no-deploy" ]]; then
  echo ""
  echo "⏭️  Mode --no-deploy : on s'arrete la (pas de deploy VPS)"
  echo ""
  exit 0
fi

echo ""
echo "🚀 Deploiement sur le VPS $VPS_HOST ..."
echo "   (tu vas devoir entrer ton mot de passe SSH)"
echo ""

ssh -t "$VPS_HOST" "
  set -e
  cd $VPS_PATH
  echo '📝 Mise a jour du tag version dans docker-compose.yml...'
  sed -i 's|image: $DOCKER_USER/habileo-backend:.*|image: $DOCKER_USER/habileo-backend:$VERSION|g' docker-compose.yml
  echo '📥 Pull des nouvelles images...'
  docker compose pull
  echo '🔄 Restart des conteneurs...'
  docker compose up -d
  echo '📊 Etat des conteneurs :'
  docker compose ps
"

# ─── Step 5 : Healthcheck final ────────────────────────────
echo ""
echo "🩺 Healthcheck de l'API publique..."
sleep 5  # laisse le temps au conteneur de redemarrer

if curl -fsS "$HEALTHCHECK_URL" > /dev/null; then
  echo "✅ $HEALTHCHECK_URL → OK"
  echo ""
  echo "🎉 Deploiement $VERSION reussi !"
else
  echo "⚠️  Le healthcheck a echoue. Verifie les logs sur le VPS :"
  echo "     ssh $VPS_HOST 'cd $VPS_PATH && docker compose logs --tail=50'"
  exit 1
fi
