# Configure and verify S3 storage on EC2 (one command from your PC).
#
# Set these before running:
#   $env:EC2_HOST     = "ec2-user@YOUR_EC2_IP"
#   $env:EC2_KEY_PATH = "C:\path\to\your-key.pem"
#
# Then:
#   .\SETUP_EC2_S3.ps1

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

$KEY_PATH = $env:EC2_KEY_PATH
$EC2_HOST = $env:EC2_HOST
$SCRIPT = Join-Path $PSScriptRoot "scripts\verify-ec2-s3.sh"

if (-not (Test-Path $SCRIPT)) {
    throw "Script not found: $SCRIPT"
}

Write-Host "Uploading verify-ec2-s3.sh to EC2..." -ForegroundColor Cyan
ssh -i $KEY_PATH $EC2_HOST "mkdir -p ~/Conversational-Document-Assistant/scripts"
scp -i $KEY_PATH $SCRIPT "${EC2_HOST}:~/Conversational-Document-Assistant/scripts/verify-ec2-s3.sh"

Write-Host "Running S3 setup and verification on EC2..." -ForegroundColor Cyan
ssh -i $KEY_PATH $EC2_HOST "chmod +x ~/Conversational-Document-Assistant/scripts/verify-ec2-s3.sh && ~/Conversational-Document-Assistant/scripts/verify-ec2-s3.sh"

Write-Host "`nS3 setup complete." -ForegroundColor Green
