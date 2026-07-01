# Quick script to connect to EC2 via SSH
#
# Set these environment variables before running:
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

icacls.exe $env:EC2_KEY_PATH /inheritance:r
icacls.exe $env:EC2_KEY_PATH /grant:r "${env:USERNAME}:R"

ssh -i $env:EC2_KEY_PATH $env:EC2_HOST
