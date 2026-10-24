@echo off
cd /d "%~dp0"
echo [Relas 2.1.5 Operational + Map Layers] Rodando testes locais obrigatorios...
echo Porta exclusiva: 8815
python selftest.py
if errorlevel 1 (
  echo.
  echo SELFTEST FALHOU. O servidor nao sera iniciado.
  pause
  exit /b 1
)
python server.py
