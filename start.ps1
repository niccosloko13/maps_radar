Set-Location $PSScriptRoot
Write-Host "[Relas 2.2.0 Road Test] Rodando testes locais obrigatorios..."
Write-Host "Porta exclusiva: 8815"
python selftest.py
if ($LASTEXITCODE -ne 0) { Write-Host "SELFTEST FALHOU. O servidor nao sera iniciado."; exit 1 }
python server.py
