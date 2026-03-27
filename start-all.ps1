# Script de Inicio Unificado para Busca Clientes
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   INICIANDO ECOSISTEMA BUSCA CLIENTES    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Obtener IP Local para informar al usuario
$localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Wi-Fi*" -or $_.InterfaceAlias -like "*Ethernet*" } | Select-Object -First 1).IPAddress
if (!$localIp) { $localIp = "localhost" }

# 1. Iniciar Orquestador (Backend)
Write-Host "[1/3] Lanzando Orquestador (Backend) [Puerto 8000]..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\activate; python main.py"

# 2. Iniciar Worker Node
Write-Host "[2/3] Lanzando Worker Node (Scraper) [Puerto 8001]..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd worker_sim; ..\backend\venv\Scripts\activate; python main.py"

# 3. Iniciar Dashboard (Frontend)
Write-Host "[3/3] Lanzando Dashboard (Vite) [Puerto 5173]..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "------------------------------------------" -ForegroundColor Yellow
Write-Host "¡Todo en marcha!" -ForegroundColor Yellow
Write-Host "Acceso Local: http://localhost:5173"
Write-Host "Acceso desde Mac/iPad: http://$($localIp):5173"
Write-Host "------------------------------------------" -ForegroundColor Yellow
Write-Host "Presione cualquier tecla para cerrar esta ventana de control..."
Pause
