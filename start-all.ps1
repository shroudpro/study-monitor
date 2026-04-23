$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$envName = "study-monitor"
$modelPath = Join-Path $backendDir "models\yolo11n-pose.onnx"
$nodeModulesPath = Join-Path $frontendDir "node_modules"

function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Get-PowerShellExecutable {
    $pwsh = Get-Command "pwsh" -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }

    $powershell = Get-Command "powershell" -ErrorAction SilentlyContinue
    if ($powershell) {
        return $powershell.Source
    }

    return $null
}

if (-not (Test-CommandExists "conda")) {
    Write-Host "未检测到 conda，请先运行 install-env.ps1 前确保 Anaconda 或 Miniconda 可用。" -ForegroundColor Red
    exit 1
}

if (-not (Test-CommandExists "npm")) {
    Write-Host "未检测到 npm，请先安装 Node.js 18 或更高版本。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $backendDir)) {
    Write-Host "未找到后端目录：$backendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $frontendDir)) {
    Write-Host "未找到前端目录：$frontendDir" -ForegroundColor Red
    exit 1
}

$envList = conda env list
$envExists = $envList | Select-String -Pattern "^\s*$envName\s+" -Quiet
if (-not $envExists) {
    Write-Host "未找到 Conda 环境：$envName" -ForegroundColor Red
    Write-Host "请先在项目根目录运行：.\install-env.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $nodeModulesPath)) {
    Write-Host "未找到前端依赖目录：$nodeModulesPath" -ForegroundColor Red
    Write-Host "请先在项目根目录运行：.\build-frontend.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $modelPath)) {
    Write-Host "未找到姿态识别模型：$modelPath" -ForegroundColor Yellow
    Write-Host "后端仍会启动，但视觉识别可能进入模拟或不可用状态。" -ForegroundColor Yellow
}

$shellExe = Get-PowerShellExecutable
if (-not $shellExe) {
    Write-Host "未检测到 PowerShell 可执行文件。" -ForegroundColor Red
    exit 1
}

$backendCommand = "Set-Location -LiteralPath '$backendDir'; Write-Host '正在启动 StudyMonitor 后端：http://localhost:8000' -ForegroundColor Cyan; conda run -n $envName python -m app.main"
$frontendCommand = "Set-Location -LiteralPath '$frontendDir'; Write-Host '正在启动 StudyMonitor 前端：http://localhost:3000' -ForegroundColor Cyan; npm run dev"

Write-Host "正在启动前后端服务，将打开两个终端窗口。" -ForegroundColor Cyan
Start-Process -FilePath $shellExe -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand)
Start-Sleep -Seconds 2
Start-Process -FilePath $shellExe -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand)

Write-Host "启动命令已发送。" -ForegroundColor Green
Write-Host "前端地址：http://localhost:3000" -ForegroundColor Green
Write-Host "后端地址：http://localhost:8000/api/health" -ForegroundColor Green
