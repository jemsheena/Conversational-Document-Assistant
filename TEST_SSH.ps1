# Test which local .pem works with your EC2 instance.
# Set EC2_IP (IP only) then run: .\TEST_SSH.ps1

$ErrorActionPreference = "Stop"

$EC2_IP = if ($env:EC2_IP) { $env:EC2_IP } else { "13.61.13.161" }
$Keys = @(
    "C:\Users\USER\Downloads\rag.pem",
    "C:\Users\USER\Downloads\fastapi-key.pem"
)
$Users = @("ec2-user", "ubuntu")

Write-Host "Testing SSH to $EC2_IP ..." -ForegroundColor Cyan

foreach ($key in $Keys) {
    if (-not (Test-Path $key)) {
        Write-Host "SKIP missing key: $key" -ForegroundColor Yellow
        continue
    }
    foreach ($user in $Users) {
        Write-Host "Trying $user @ $EC2_IP with $(Split-Path $key -Leaf) ..." -NoNewline
        $out = ssh -i $key -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 "${user}@${EC2_IP}" "echo SSH_OK" 2>&1
        if ($LASTEXITCODE -eq 0 -and $out -match "SSH_OK") {
            Write-Host " SUCCESS" -ForegroundColor Green
            Write-Host ""
            Write-Host "Use these GitHub secrets:" -ForegroundColor Green
            Write-Host "  EC2_HOST = $EC2_IP"
            Write-Host "  EC2_USER = $user"
            Write-Host "  EC2_SSH_KEY = full contents of $key"
            exit 0
        }
        $msg = ($out | Out-String).Trim()
        if ($msg) { Write-Host " FAIL ($msg)" -ForegroundColor Red }
        else { Write-Host " FAIL (timeout or no route)" -ForegroundColor Red }
    }
}

Write-Host ""
Write-Host "No working key/user combo found." -ForegroundColor Red
Write-Host "Check: EC2 running, security group allows SSH (port 22), correct key pair on instance."
exit 1
