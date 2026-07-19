# Full deploy to EC2 (manual fallback — prefer automated CI/CD deploy)
#
# Automated path: push to main with EC2_DEPLOY_ENABLED=true and GitHub secrets set.
# See .github/workflows/ci-cd.yml
#
# Set these environment variables before running (never commit keys to git):
#   $env:EC2_HOST     = "ec2-user@YOUR_EC2_IP"
#   $env:EC2_KEY_PATH = "C:\path\to\your-key.pem"

$ErrorActionPreference = "Stop"

if (-not $env:EC2_HOST) {
    throw "EC2_HOST is not set. Example: `$env:EC2_HOST = 'ec2-user@1.2.3.4'"
}
if (-not $env:EC2_KEY_PATH) {
    throw "EC2_KEY_PATH is not set. Example: `$env:EC2_KEY_PATH = 'C:\path\to\key.pem'"
}
if (-not (Test-Path $env:EC2_KEY_PATH)) {
    throw "SSH key not found: $($env:EC2_KEY_PATH)"
}

$EC2_HOST = $env:EC2_HOST
$KEY_PATH = $env:EC2_KEY_PATH
$ARCHIVE = "deploy_latest.tar.gz"

Set-Location $PSScriptRoot

Write-Host "Step 1: Build deployment archive..." -ForegroundColor Cyan
tar --exclude="frontend/node_modules" --exclude="backend/.venv" --exclude="backend/venv" --exclude="backend/backend/venv" --exclude=".git" --exclude="backend/data" --exclude="data" --exclude="*.tar.gz" -czf $ARCHIVE .

Write-Host "Step 2: Upload archive to EC2..." -ForegroundColor Cyan
scp -i $KEY_PATH $ARCHIVE "${EC2_HOST}:~/deploy_latest.tar.gz"

Write-Host "Step 3: Extract and run Docker Compose on EC2..." -ForegroundColor Cyan
ssh -i $KEY_PATH $EC2_HOST @"
set -e
if ! docker compose version >/dev/null 2>&1; then
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -fsSL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi
docker ps -q | xargs -r docker stop
sudo rm -rf ~/Conversational-Document-Assistant && mkdir -p ~/Conversational-Document-Assistant
tar -xzf ~/deploy_latest.tar.gz -C ~/Conversational-Document-Assistant
cd ~/Conversational-Document-Assistant
docker compose down || true
docker compose up --build -d
docker compose ps
"@

Write-Host "Deployment complete." -ForegroundColor Green
