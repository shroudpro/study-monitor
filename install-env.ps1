$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $projectRoot "environment.yml"
$envName = "study-monitor"

function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "conda")) {
    Write-Host "未检测到 conda，请先安装 Anaconda 或 Miniconda，并重新打开 PowerShell。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Host "未找到 environment.yml：$envFile" -ForegroundColor Red
    exit 1
}

Write-Host "正在检查 Conda 环境：$envName" -ForegroundColor Cyan
$envList = conda env list
$envExists = $envList | Select-String -Pattern "^\s*$envName\s+" -Quiet

if ($envExists) {
    Write-Host "环境已存在，正在根据 environment.yml 更新依赖..." -ForegroundColor Yellow
    conda env update -n $envName -f $envFile --prune
} else {
    Write-Host "环境不存在，正在创建 Conda 环境..." -ForegroundColor Green
    conda env create -f $envFile
}

Write-Host "Conda 环境准备完成：$envName" -ForegroundColor Green
Write-Host "如需手动进入环境，请运行：conda activate $envName" -ForegroundColor Cyan
