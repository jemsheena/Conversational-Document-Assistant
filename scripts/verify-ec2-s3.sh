#!/usr/bin/env bash
# Configure and verify S3 PDF storage on EC2.
# Run on the server: ./scripts/verify-ec2-s3.sh
# Or from Windows: .\SETUP_EC2_S3.ps1

set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/Conversational-Document-Assistant}"
ENV_FILE="$APP_DIR/.env"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
AWS_REGION="${AWS_REGION:-eu-north-1}"
S3_BUCKET="${S3_BUCKET:-conversational-doc-assistant-pdfs}"
S3_PREFIX="${S3_PREFIX:-pdfs/}"

set_env() {
  local key="$1"
  local val="$2"
  mkdir -p "$APP_DIR"
  touch "$ENV_FILE"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

echo "==> Configuring S3 in $ENV_FILE"
set_env STORAGE_BACKEND s3
set_env AWS_REGION "$AWS_REGION"
set_env S3_BUCKET "$S3_BUCKET"
set_env S3_PREFIX "$S3_PREFIX"

echo ""
echo "==> S3 settings in .env:"
grep -E '^(STORAGE_BACKEND|AWS_REGION|S3_BUCKET|S3_PREFIX)=' "$ENV_FILE" || true

echo ""
echo "==> IAM role on this instance (needs AmazonS3FullAccess):"
if curl -sf --max-time 2 http://169.254.169.254/latest/meta-data/iam/info >/dev/null 2>&1; then
  curl -s http://169.254.169.254/latest/meta-data/iam/info | grep -o '"InstanceProfileArn":"[^"]*"' || \
    curl -s http://169.254.169.254/latest/meta-data/iam/info
else
  echo "WARNING: No IAM role detected on this EC2 instance."
  echo "         Attach ec2-s3-pdf-access (AmazonS3FullAccess) in the AWS console."
fi

if [ ! -f "$APP_DIR/$COMPOSE_FILE" ]; then
  echo ""
  echo "ERROR: $APP_DIR/$COMPOSE_FILE not found."
  echo "       Deploy the app first (CI/CD or UPLOAD_TO_EC2.ps1)."
  exit 1
fi

echo ""
echo "==> Restarting containers..."
cd "$APP_DIR"
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "==> Waiting for backend..."
sleep 8

echo ""
echo "==> Backend storage mode:"
if docker compose -f "$COMPOSE_FILE" logs backend 2>&1 | grep -q "PDF storage: s3"; then
  echo "OK — PDF storage: s3"
else
  echo "FAIL — expected 'PDF storage: s3' in backend logs:"
  docker compose -f "$COMPOSE_FILE" logs backend 2>&1 | grep -i "PDF storage" || \
    docker compose -f "$COMPOSE_FILE" logs --tail=30 backend
  exit 1
fi

echo ""
echo "==> S3 bucket access test:"
if docker compose -f "$COMPOSE_FILE" exec -T backend python -c "
import boto3, os, sys
bucket = os.environ.get('S3_BUCKET', '$S3_BUCKET')
region = os.environ.get('AWS_REGION', '$AWS_REGION')
prefix = os.environ.get('S3_PREFIX', '$S3_PREFIX')
client = boto3.client('s3', region_name=region)
client.head_bucket(Bucket=bucket)
resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=5)
count = resp.get('KeyCount', 0)
print(f'OK — bucket {bucket} reachable, {count} object(s) under {prefix}')
"; then
  :
else
  echo "FAIL — cannot reach S3. Check IAM role and bucket region."
  exit 1
fi

echo ""
echo "==> Container status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "Done. Upload a PDF in the app, then check s3://$S3_BUCKET/$S3_PREFIX in AWS console."
