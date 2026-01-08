# PowerShell script to download vendor files for Windows users
$vendors = @(
    @{ url = 'https://cdn.tailwindcss.com'; dest = 'static/vendor/tailwind.js' },
    @{ url = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'; dest = 'static/vendor/fontawesome.min.css' },
    @{ url = 'https://unpkg.com/htmx.org@1.9.10'; dest = 'static/vendor/htmx.min.js' },
    @{ url = 'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js'; dest = 'static/vendor/alpine.min.js' }
)

foreach ($v in $vendors) {
    $url = $v.url
    $dest = $v.dest
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Write-Host "Downloading $url -> $dest"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
        Write-Host "  OK"
    } catch {
        Write-Host "  ERROR: $_"
    }
}
Write-Host "Done. Verify files exist under static/vendor/ and restart the dev server."