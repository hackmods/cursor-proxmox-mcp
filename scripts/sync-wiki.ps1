# Sync docs/wiki/*.md to the GitHub wiki for hackmods/cursor-proxmox-mcp.
# Requires: gh auth, wiki enabled. First page must exist in the GitHub UI.
$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$WikiSrc = Join-Path $RepoRoot "docs\wiki"
$Tmp = Join-Path $env:TEMP ("cursor-proxmox-mcp-wiki-" + [guid]::NewGuid().ToString("n"))
$WikiRemote = "https://github.com/hackmods/cursor-proxmox-mcp.wiki.git"

if (-not (Test-Path $WikiSrc)) { throw "Missing $WikiSrc" }

Write-Host "Cloning wiki at $Tmp ..."
git clone --depth 1 $WikiRemote $Tmp
if (-not (Test-Path (Join-Path $Tmp ".git"))) {
    Write-Host @"
ERROR: Wiki remote not found ($WikiRemote).

GitHub only creates the wiki git repo after the first page exists.
1. Open https://github.com/hackmods/cursor-proxmox-mcp/wiki
2. Click 'Create the first page' and save (content can be temporary).
3. Re-run this script.

Source markdown remains in docs/wiki/ in the main repo.
"@
    exit 1
}

Get-ChildItem (Join-Path $WikiSrc "*.md") |
    Where-Object { $_.Name -ne "README.md" } |
    ForEach-Object { Copy-Item $_.FullName $Tmp -Force }

Push-Location $Tmp
# Drop repo-only README if it landed somehow
if (Test-Path "README.md") { Remove-Item "README.md" -Force }
git add -- *.md
$status = git status --porcelain
if (-not $status) {
    Write-Host "Wiki already up to date."
    Pop-Location
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
    exit 0
}
git -c user.email="wiki-bot@local" -c user.name="wiki-sync" commit -m "docs: sync wiki from docs/wiki"
git -c credential.helper="!gh auth git-credential" push -u origin HEAD:master
if ($LASTEXITCODE -ne 0) {
    # Some wikis use main
    git -c credential.helper="!gh auth git-credential" push -u origin HEAD:main
}
Pop-Location
Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
Write-Host "Wiki synced."
