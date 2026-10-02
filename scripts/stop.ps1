# Para backend + frontend iniciados pelo start.ps1
$pidsFile = "$PSScriptRoot\..\pids"
if (-not (Test-Path $pidsFile)) {
    $pidsFile = "$PSScriptRoot\..\.pids"
}

if (Test-Path $pidsFile) {
    $ids = (Get-Content $pidsFile) -split ","
    foreach ($id in $ids) {
        $id = $id.Trim()
        if ($id -match '^\d+$') {
            try {
                Stop-Process -Id ([int]$id) -Force -ErrorAction SilentlyContinue
                Write-Host "Encerrado PID $id" -ForegroundColor Yellow
            } catch {
                Write-Host "PID $id já estava encerrado." -ForegroundColor Gray
            }
        }
    }
    Remove-Item $pidsFile -Force
    Write-Host "Pronto." -ForegroundColor Green
} else {
    Write-Host "Nenhum PID salvo. Feche as janelas manualmente." -ForegroundColor Yellow
}
