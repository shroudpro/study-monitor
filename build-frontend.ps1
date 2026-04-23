$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $projectRoot "frontend"

function Test-CommandExists {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "npm")) {
    Write-Host "未检测到 npm，请先安装 Node.js 18 或更高版本。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $frontendDir)) {
    Write-Host "未找到前端目录：$frontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir
try {
    if (Test-Path -LiteralPath "package-lock.json") {
        Write-Host "正在使用 package-lock.json 安装前端依赖..." -ForegroundColor Cyan
        npm ci
    } else {
        Write-Host "未找到 package-lock.json，正在执行 npm install..." -ForegroundColor Cyan
        npm install
    }

    Write-Host "正在编译前端..." -ForegroundColor Cyan
    npm run build
    Write-Host "前端编译完成。" -ForegroundColor Green
} finally {
    Pop-Location
}
