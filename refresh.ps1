#Requires -Version 5.1
<#
.SYNOPSIS
  ينضّف مشروع الـ Backend ويعيد تثبيته من الصفر (حل مشاكل المكتبات بعد git pull).

.USAGE
  .\refresh.ps1
  .\refresh.ps1 -SkipPull
  .\refresh.ps1 -SkipRag
#>
param(
  [switch]$SkipPull,
  [switch]$SkipRag
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Write-Step([string]$Message) {
  Write-Host ""
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Remove-PathSafe([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    Write-Host "  remove: $Path"
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
  }
}

Write-Host ""
Write-Host "Odoo-Generation Backend — Clean & Refresh" -ForegroundColor Green
Write-Host "Folder: $PSScriptRoot"

if (-not $SkipPull) {
  Write-Step "Updating from git (git pull)"
  if (Test-Path .git) {
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
      Write-Host "WARNING: git pull failed. Continue with local clean/install..." -ForegroundColor Yellow
    }
  } else {
    Write-Host "Not a git repo — skip pull"
  }
}

Write-Step "Cleaning junk / caches / old virtualenv"
Remove-PathSafe ".venv"
Remove-PathSafe "venv"
Remove-PathSafe "__pycache__"
Remove-PathSafe ".pytest_cache"
Remove-PathSafe "chroma_db"
Remove-PathSafe "jobs_state.json"
Remove-PathSafe "commit_a27f229"

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
  ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }

Get-ChildItem -Path . -Recurse -Include "*.pyc","*.pyo" -File -ErrorAction SilentlyContinue |
  ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }

Write-Step "Finding Python"
$python = $null
$probes = @(
  @{ Exe = "py"; Args = @("-3.12", "-c", "import sys; print(sys.executable)") },
  @{ Exe = "py"; Args = @("-3.11", "-c", "import sys; print(sys.executable)") },
  @{ Exe = "py"; Args = @("-3", "-c", "import sys; print(sys.executable)") },
  @{ Exe = "python"; Args = @("-c", "import sys; print(sys.executable)") }
)
foreach ($probe in $probes) {
  try {
    if (-not (Get-Command $probe.Exe -ErrorAction SilentlyContinue)) { continue }
    $out = & $probe.Exe @($probe.Args) 2>$null
    if ($LASTEXITCODE -eq 0 -and $out) {
      $candidatePath = ($out | Select-Object -Last 1).ToString().Trim()
      if (Test-Path -LiteralPath $candidatePath) {
        $python = $candidatePath
        break
      }
    }
  } catch {
    # try next
  }
}

if (-not $python) {
  Write-Host "ERROR: Python not found. Install Python 3.11+ and retry." -ForegroundColor Red
  exit 1
}

$ver = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  Using: $python (Python $ver)"

Write-Step "Creating fresh virtualenv (.venv)"
& $python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv" }

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$venvPip = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"
if (-not (Test-Path $venvPython)) {
  throw "venv python missing: $venvPython"
}

Write-Step "Upgrading pip"
& $venvPython -m pip install --upgrade pip setuptools wheel

if (-not (Test-Path "requirements.txt")) {
  throw "requirements.txt not found"
}

if ($SkipRag) {
  Write-Step "Installing core requirements (without RAG / ML packages)"
  $core = @(
    "fastapi",
    "uvicorn[standard]",
    "jinja2",
    "pydantic",
    "python-dotenv",
    "google-genai",
    "openai",
    "httpx"
  )
  & $venvPip install @core
} else {
  Write-Step "Installing requirements.txt (full)"
  & $venvPip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Full install failed (often chromadb / sentence-transformers / torch)." -ForegroundColor Yellow
    Write-Host "Retrying core packages only so the API can still run..." -ForegroundColor Yellow
    $core = @(
      "fastapi",
      "uvicorn[standard]",
      "jinja2",
      "pydantic",
      "python-dotenv",
      "google-genai",
      "openai",
      "httpx"
    )
    & $venvPip install @core
    if ($LASTEXITCODE -ne 0) { throw "Core install failed" }
    Write-Host "Core install OK. RAG optional packages skipped." -ForegroundColor Yellow
  }
}

if (-not (Test-Path ".env")) {
  if (Test-Path ".env.example") {
    Write-Step "Creating .env from .env.example (fill your API keys)"
    Copy-Item ".env.example" ".env"
  } else {
    Write-Host "WARNING: No .env file. Create one with your AI keys." -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "DONE. Backend is fresh." -ForegroundColor Green
Write-Host "Start with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Write-Host ""
