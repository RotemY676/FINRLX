# ============================================================
# FinRL-X CPU-only Research Container — PowerShell
# ============================================================
# LOCAL RESEARCH ONLY — not used by Railway production.
# No broker execution. No live RL. No production influence.
# ============================================================

param(
    [string]$Algorithm = "PPO",
    [int]$Timesteps = 200,
    [int]$Seed = 42,
    [switch]$SaveModel
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResearchDir = Split-Path -Parent $ScriptDir
$ImageName = "finrlx-cpu-research"

Write-Host "============================================================"
Write-Host "FinRL-X CPU-only Research Container"
Write-Host "LOCAL RESEARCH ONLY — no production influence"
Write-Host "============================================================"
Write-Host ""

# Build
Write-Host "Building research image..."
docker build -t $ImageName $ResearchDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed. Is Docker running?"
    exit 1
}

# Run
$cmd = @(
    "python", "train_cpu_rl.py",
    "--algorithm", $Algorithm,
    "--timesteps", $Timesteps.ToString(),
    "--seed", $Seed.ToString(),
    "--output-dir", "/research/outputs"
)
if ($SaveModel) {
    $cmd += "--save-model"
}

$OutputsDir = Join-Path $ResearchDir "outputs"
if (-not (Test-Path $OutputsDir)) {
    New-Item -ItemType Directory -Path $OutputsDir | Out-Null
}

Write-Host "Running: $($cmd -join ' ')"
Write-Host ""

docker run --rm `
    -v "${OutputsDir}:/research/outputs" `
    $ImageName @cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Research complete. Artifacts in: $OutputsDir"
    Write-Host "These artifacts are LOCAL RESEARCH ONLY."
} else {
    Write-Host "Research container exited with error code $LASTEXITCODE"
    exit $LASTEXITCODE
}
