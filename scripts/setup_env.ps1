if (Test-Path .env) {
    Write-Host ".env already exists. Leaving it unchanged."
    exit 0
}

Copy-Item .env.example .env
Write-Host "Created .env from .env.example. Fill in real provider keys when needed."
