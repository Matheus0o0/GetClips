Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$ROOT = $PSScriptRoot

function Kill-Porta([int]$porta) {
    netstat -ano | Select-String ":$porta\s" | ForEach-Object {
        $pid_ = ($_ -split '\s+')[-1]
        if ($pid_ -match '^\d+$') {
            Stop-Process -Id ([int]$pid_) -Force -ErrorAction SilentlyContinue
        }
    }
}

# Mata instâncias anteriores
Kill-Porta 8000
Kill-Porta 3000
if (Test-Path "$ROOT\.pids") {
    Get-Content "$ROOT\.pids" | ForEach-Object {
        $_ -split ',' | ForEach-Object {
            if ($_ -match '^\d+$') { Stop-Process -Id ([int]$_) -Force -ErrorAction SilentlyContinue }
        }
    }
}

# Ícone: círculo verde 32x32
$bmp = [System.Drawing.Bitmap]::new(32, 32)
$g   = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.FillRectangle([System.Drawing.Brushes]::Black, 0, 0, 32, 32)
$g.FillEllipse([System.Drawing.Brushes]::LimeGreen, 3, 3, 26, 26)
$g.Dispose()

$notify = [System.Windows.Forms.NotifyIcon]::new()
$notify.Icon    = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
$notify.Text    = 'TranscreverVideo'
$notify.Visible = $true

function Abrir-Browser { Start-Process 'http://localhost:3000' }

function Parar-Tudo {
    Kill-Porta 8000
    Kill-Porta 3000
    Stop-Process -Name 'ollama' -Force -ErrorAction SilentlyContinue
    Remove-Item "$ROOT\.pids" -ErrorAction SilentlyContinue
    $notify.Visible = $false
    $bmp.Dispose()
    [System.Windows.Forms.Application]::Exit()
}

$menu = [System.Windows.Forms.ContextMenuStrip]::new()
[void]$menu.Items.Add('Abrir no browser',  $null, { Abrir-Browser })
[void]$menu.Items.Add([System.Windows.Forms.ToolStripSeparator]::new())
[void]$menu.Items.Add('Parar tudo',        $null, { Parar-Tudo })
$notify.ContextMenuStrip = $menu
$notify.add_MouseDoubleClick({
    if ($_.Button -eq [System.Windows.Forms.MouseButtons]::Left) { Abrir-Browser }
})

# Inicia serviços em background (sem terminais)
$r = $ROOT
$bgScript = {
    param($r)
    Start-Process 'ollama' 'serve' -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep 2
    $b = Start-Process "$r\backend\.venv\Scripts\python.exe" `
        '-m uvicorn app.main:app --port 8000 --host 127.0.0.1 --loop asyncio' `
        -WorkingDirectory "$r\backend" -PassThru -WindowStyle Hidden
    Start-Sleep 4
    $f = Start-Process 'cmd' '/c npm run dev' `
        -WorkingDirectory "$r\frontend" -PassThru -WindowStyle Hidden
    "$($b.Id),$($f.Id)" | Set-Content "$r\.pids" -Encoding utf8
    Start-Sleep 5
    Start-Process 'http://localhost:3000'
}

$ps = [powershell]::Create()
[void]$ps.AddScript($bgScript).AddParameter('r', $r)
[void]$ps.BeginInvoke()

$notify.ShowBalloonTip(4000, 'TranscreverVideo', 'Iniciando... aguarde ~10s', [System.Windows.Forms.ToolTipIcon]::Info)

[System.Windows.Forms.Application]::Run()
