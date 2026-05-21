<#
.SYNOPSIS
  Semi-automated Google OAuth setup for FINRLX.

.DESCRIPTION
  Automates everything the gcloud + railway CLIs can do. The one step
  Google does NOT expose via CLI is creating the OAuth 2.0 *Web*
  Client ID with custom redirect URIs — that has to happen in the
  Console UI. The script opens the right page for you, then accepts
  the Client ID + Secret you paste back and writes them to
  backend/.env and (optionally) Railway env vars.

.PARAMETER ProjectPrefix
  Base name used for the GCP project. A short random suffix is added
  so the project ID is globally unique. Default: "finrlx".

.PARAMETER FrontendUrl
  Public URL of the deployed frontend (without trailing slash).
  Example: "https://finrlx-frontend.up.railway.app". If omitted,
  the script asks interactively.

.PARAMETER BackendUrl
  Public URL of the deployed backend (without trailing slash).
  Example: "https://finrlx-backend.up.railway.app". If omitted,
  the script asks interactively.

.PARAMETER SupportEmail
  Required by Google for the OAuth consent screen. Must be an
  address you can reach. If omitted, the script asks interactively.

.PARAMETER SkipRailway
  Skip the "set Railway env vars" step entirely. Default $false.

.EXAMPLE
  .\setup_google_oauth.ps1

.EXAMPLE
  .\setup_google_oauth.ps1 `
      -FrontendUrl "https://finrlx-frontend.up.railway.app" `
      -BackendUrl  "https://finrlx-backend.up.railway.app" `
      -SupportEmail "you@example.com"

.NOTES
  Prerequisites:
    1. gcloud CLI installed and on PATH (https://cloud.google.com/sdk).
    2. (Optional) railway CLI logged in: `railway login`.
    3. A Google account that can create GCP projects + a domain you
       control or accept the default Gmail address as the support email.
#>

[CmdletBinding()]
param(
    [string]$ProjectPrefix = "finrlx",
    [string]$FrontendUrl,
    [string]$BackendUrl,
    [string]$SupportEmail,
    [switch]$SkipRailway
)

$ErrorActionPreference = "Stop"

# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

function Write-Step([string]$Msg) {
    Write-Host ""
    Write-Host "===> $Msg" -ForegroundColor Cyan
}

function Write-Warn([string]$Msg) {
    Write-Host "!!  $Msg" -ForegroundColor Yellow
}

function Write-Done([string]$Msg) {
    Write-Host "OK  $Msg" -ForegroundColor Green
}

function Assert-CommandExists([string]$Cmd, [string]$InstallHint) {
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Write-Host ""
        Write-Host "Required CLI '$Cmd' not found on PATH." -ForegroundColor Red
        Write-Host $InstallHint
        exit 1
    }
}

function Prompt-NonEmpty([string]$Label, [string]$DefaultValue = $null) {
    while ($true) {
        if ($DefaultValue) {
            $value = Read-Host "$Label [$DefaultValue]"
            if (-not $value) { $value = $DefaultValue }
        } else {
            $value = Read-Host $Label
        }
        if ($value) { return $value }
        Write-Warn "Cannot be empty."
    }
}

function Prompt-YesNo([string]$Label, [string]$Default = "y") {
    $hint = if ($Default -eq "y") { "[Y/n]" } else { "[y/N]" }
    while ($true) {
        $r = Read-Host "$Label $hint"
        if (-not $r) { $r = $Default }
        switch ($r.ToLower()) {
            "y" { return $true }
            "yes" { return $true }
            "n" { return $false }
            "no" { return $false }
            default { Write-Warn "Please answer y or n." }
        }
    }
}

function Get-RepoRoot() {
    # script location -> ../  (scripts/ is one level under repo root)
    $scriptDir = Split-Path -Parent $MyInvocation.PSCommandPath
    return Resolve-Path (Join-Path $scriptDir "..")
}

function Update-EnvFile([string]$Path, [hashtable]$Pairs) {
    # Preserve existing lines + insert/replace keys idempotently.
    $existing = @()
    if (Test-Path $Path) {
        $existing = Get-Content -Path $Path -Encoding UTF8
    }
    $existingKeys = @{}
    $output = @()
    foreach ($line in $existing) {
        # Match KEY=VALUE on non-comment lines
        if ($line -match '^\s*([A-Z0-9_]+)\s*=') {
            $key = $Matches[1]
            if ($Pairs.ContainsKey($key)) {
                $output += "$key=$($Pairs[$key])"
                $existingKeys[$key] = $true
                continue
            }
        }
        $output += $line
    }
    foreach ($key in $Pairs.Keys) {
        if (-not $existingKeys.ContainsKey($key)) {
            $output += "$key=$($Pairs[$key])"
        }
    }
    Set-Content -Path $Path -Value $output -Encoding UTF8
}

# ────────────────────────────────────────────────────────────────────
# Preflight
# ────────────────────────────────────────────────────────────────────

Write-Step "Preflight checks"
Assert-CommandExists "gcloud" "Install: https://cloud.google.com/sdk/docs/install"
Write-Done "gcloud found"

$hasRailwayCli = (Get-Command "railway" -ErrorAction SilentlyContinue) -ne $null
if ($hasRailwayCli) {
    Write-Done "railway CLI found"
} else {
    Write-Warn "railway CLI not found. We'll skip auto-setting Railway env vars at the end."
    Write-Warn "Install later: https://docs.railway.app/develop/cli"
}

# gcloud auth
Write-Step "Checking gcloud authentication"
$activeAccount = (& gcloud auth list --filter="status:ACTIVE" --format="value(account)") 2>$null
if (-not $activeAccount) {
    Write-Host "You're not signed in to gcloud. Launching browser..."
    & gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "gcloud auth failed." -ForegroundColor Red
        exit 1
    }
    $activeAccount = (& gcloud auth list --filter="status:ACTIVE" --format="value(account)")
}
Write-Done "Signed in as $activeAccount"

# Interactive params
if (-not $SupportEmail) {
    $SupportEmail = Prompt-NonEmpty "OAuth consent screen support email" $activeAccount
}
if (-not $FrontendUrl) {
    $FrontendUrl = Prompt-NonEmpty "Frontend URL (e.g. https://finrlx-frontend.up.railway.app)"
}
if (-not $BackendUrl) {
    $BackendUrl = Prompt-NonEmpty "Backend URL (e.g. https://finrlx-backend.up.railway.app)"
}

$FrontendUrl = $FrontendUrl.TrimEnd("/")
$BackendUrl  = $BackendUrl.TrimEnd("/")

# ────────────────────────────────────────────────────────────────────
# Project creation
# ────────────────────────────────────────────────────────────────────

Write-Step "Creating GCP project"
# Project IDs must be globally unique. Suffix with 6 random hex chars.
$suffix = -join ((0..5) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 16) })
$projectId = "$ProjectPrefix-$suffix"
Write-Host "Project ID: $projectId"
$confirm = Prompt-YesNo "Create this project now?" "y"
if (-not $confirm) {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

& gcloud projects create $projectId --name="FINRLX" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Project creation failed. If the ID exists, re-run to get a new suffix." -ForegroundColor Red
    exit 1
}
Write-Done "Created project $projectId"

& gcloud config set project $projectId --quiet | Out-Null
Write-Done "Set $projectId as active project"

# ────────────────────────────────────────────────────────────────────
# Enable APIs
# ────────────────────────────────────────────────────────────────────

Write-Step "Enabling required APIs"
$apis = @(
    "iamcredentials.googleapis.com",
    "iap.googleapis.com",
    "oauth2.googleapis.com"
)
foreach ($api in $apis) {
    & gcloud services enable $api --project=$projectId --quiet | Out-Null
    Write-Done "Enabled $api"
}

# ────────────────────────────────────────────────────────────────────
# OAuth consent screen (brand)
# ────────────────────────────────────────────────────────────────────

Write-Step "Creating OAuth consent brand"
# Note: only the *brand* part is automatable via gcloud iap oauth-brands.
# The Web Client ID below is NOT (Google blocks it on CLI/API). Brand
# creation may fail if one already exists for the project -> tolerate.
& gcloud iap oauth-brands create `
    --application_title="FINRLX" `
    --support_email=$SupportEmail `
    --project=$projectId 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Brand creation returned non-zero. This is OK if a brand already exists or if the org policy blocks gcloud-side brand creation. Continuing — the manual Console step below will handle it either way."
} else {
    Write-Done "OAuth consent brand created"
}

# ────────────────────────────────────────────────────────────────────
# Manual step: create OAuth 2.0 Web Client ID
# ────────────────────────────────────────────────────────────────────

Write-Step "MANUAL STEP — create the OAuth 2.0 Web Client ID"
Write-Host @"
Google does NOT expose creation of OAuth 2.0 Web Client IDs (the kind
with custom redirect URIs) via CLI or API. You must do this one step
in the browser. The Console will open at the right page in 3 seconds.

When you're there:

  1. If asked, configure the OAuth consent screen:
       User Type:         External
       App name:          FINRLX
       User support email: $SupportEmail
       Developer contact: $SupportEmail
       Scopes:            leave default (we only need openid, email, profile)
       Test users:        add every Gmail address you want to admit to the beta
  2. APIs & Services -> Credentials -> Create Credentials -> OAuth Client ID
  3. Application type:   Web application
  4. Name:               FINRLX backend
  5. Authorized JavaScript origins (paste exactly):
       $FrontendUrl
       http://localhost:3000
  6. Authorized redirect URIs (paste exactly):
       $BackendUrl/api/v1/auth/google/callback
       http://localhost:8000/api/v1/auth/google/callback
  7. Click Create. Copy the Client ID and Client Secret.

"@ -ForegroundColor Yellow

Start-Sleep -Seconds 3
$consoleUrl = "https://console.cloud.google.com/apis/credentials?project=$projectId"
Write-Host "Opening: $consoleUrl"
Start-Process $consoleUrl

# ────────────────────────────────────────────────────────────────────
# Collect credentials
# ────────────────────────────────────────────────────────────────────

Write-Step "Paste the credentials back here"
$clientId = Prompt-NonEmpty "Client ID (ends with .apps.googleusercontent.com)"
if (-not $clientId.EndsWith(".apps.googleusercontent.com")) {
    Write-Warn "Client ID doesn't end with .apps.googleusercontent.com — double-check before continuing."
    if (-not (Prompt-YesNo "Proceed anyway?" "n")) {
        exit 1
    }
}

$secretSecure = Read-Host "Client Secret" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSecure)
$clientSecret = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR) | Out-Null

if (-not $clientSecret) {
    Write-Host "Client Secret cannot be empty." -ForegroundColor Red
    exit 1
}

$redirectUri      = "$BackendUrl/api/v1/auth/google/callback"
$postLoginRedirect = "$FrontendUrl/login/google-finish"

# ────────────────────────────────────────────────────────────────────
# Write backend/.env
# ────────────────────────────────────────────────────────────────────

Write-Step "Updating backend/.env"
$repoRoot = Get-RepoRoot
$envPath = Join-Path $repoRoot "backend/.env"
$pairs = @{
    "GOOGLE_OAUTH_CLIENT_ID"            = $clientId
    "GOOGLE_OAUTH_CLIENT_SECRET"        = $clientSecret
    "GOOGLE_OAUTH_REDIRECT_URI"         = $redirectUri
    "GOOGLE_OAUTH_POST_LOGIN_REDIRECT"  = $postLoginRedirect
}
Update-EnvFile -Path $envPath -Pairs $pairs
Write-Done "Wrote 4 keys to $envPath"

# ────────────────────────────────────────────────────────────────────
# Set Railway env vars
# ────────────────────────────────────────────────────────────────────

if ($hasRailwayCli -and -not $SkipRailway) {
    Write-Step "Setting Railway env vars"
    if (Prompt-YesNo "Run 'railway variables set' for the 4 keys now? (You must be linked to the backend service.)" "y") {
        $railwayArgs = @(
            "variables", "set",
            "GOOGLE_OAUTH_CLIENT_ID=$clientId",
            "GOOGLE_OAUTH_CLIENT_SECRET=$clientSecret",
            "GOOGLE_OAUTH_REDIRECT_URI=$redirectUri",
            "GOOGLE_OAUTH_POST_LOGIN_REDIRECT=$postLoginRedirect"
        )
        & railway @railwayArgs
        if ($LASTEXITCODE -eq 0) {
            Write-Done "Railway env vars set. Redeploy the backend service to pick them up."
        } else {
            Write-Warn "railway variables set returned non-zero. Set the four keys manually in the Railway dashboard or via 'railway link'+'railway variables set'."
        }
    } else {
        Write-Warn "Skipped Railway. Set the 4 keys manually in the Railway dashboard."
    }
} else {
    Write-Warn "Skipping Railway step (CLI not installed or -SkipRailway). Set the 4 keys manually in the Railway dashboard."
}

# ────────────────────────────────────────────────────────────────────
# Smoke
# ────────────────────────────────────────────────────────────────────

Write-Step "Done"
Write-Host @"

What just happened:
  Project:       $projectId
  Brand:         FINRLX (support: $SupportEmail)
  Local env:     $envPath
  Backend URL:   $BackendUrl
  Frontend URL:  $FrontendUrl
  Redirect URI:  $redirectUri

Next:
  1. Redeploy the backend service so it loads the new env vars.
  2. Open $FrontendUrl/login and click 'Sign in with Google'.
  3. You should bounce through Google -> .../login/google-finish#... -> /.

If the redirect bounces to '/login/google-finish?error=...':
  - error=state mismatch         CSRF cookie didn't match. Try again.
  - error=not_allowlisted        Add the Gmail to email_allowlist:
                                   python -m scripts.manage_allowlist add <email>
  - error=verification:...       id_token signature/issuer failed; usually
                                   means the wrong Client ID was pasted.

"@ -ForegroundColor Cyan
