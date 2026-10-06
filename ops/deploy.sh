#!/bin/bash
# Déploie SECOMO sur le cluster k3d : import des images, puis application des manifestes.
# Usage : ops/deploy.sh <tag>      (les images secomo-backend:<tag> et secomo-frontend:<tag> doivent exister)
set -euo pipefail

TAG="${1:?usage : deploy.sh <tag>}"
CLUSTER="${K3D_CLUSTER:-secomo}"
cd "$(dirname "$0")/.."

echo "📦 Import des images dans le cluster $CLUSTER"
k3d image import "secomo-backend:$TAG" "secomo-frontend:$TAG" -c "$CLUSTER"

echo "🚀 Application des manifestes"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl create configmap grafana-dashboards -n secomo \
  --from-file=k8s/monitoring/dashboards/ --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/monitoring/
# Grafana ne relit sa configuration et ses tableaux de bord qu'au démarrage
kubectl rollout restart deployment/grafana -n secomo
for f in backend frontend; do
  sed "s/IMAGE_TAG/$TAG/" "k8s/$f.yaml" | kubectl apply -f -
done
kubectl apply -f k8s/ingress.yaml

echo "⏳ Attente du déploiement"
kubectl rollout status deployment/postgres -n secomo --timeout=180s
kubectl rollout status deployment/backend -n secomo --timeout=300s
kubectl rollout status deployment/frontend -n secomo --timeout=180s
echo "✅ SECOMO $TAG déployé : http://localhost:8081"
