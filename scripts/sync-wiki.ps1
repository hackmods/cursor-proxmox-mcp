# Sync docs/wiki/*.md to the GitHub wiki for hackmods/cursor-proxmox-mcp.
# Requires: gh auth, wiki enabled. First push initializes an empty wiki.
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$WikiSrc = Join-Path $RepoRoot "docs\wiki"
$Tmp = Join-Path $env:TEMP ("cursor-proxmox-mcp-wiki-" + [guid]::NewGuid().ToString("n"))
$WikiRemote = "https://github.com/hackmods/cursor-proxmox-mcp.wiki.git"

if (-not (Test-Path $WikiSrc)) { throw "Missing $WikiSrc" }

Write-Host "Cloning wiki at $Tmp ..."
git clone --depth 1 $WikiRemote $Tmp 2>&1 | Out-Null
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

Copy-Item (Join-Path $WikiSrc "*.md") $Tmp -Force
Push-Location $Tmp
git add *.md
if (-not (git status --porcelain)) {
    Write-Host "Wiki already up to date."
    Pop-Location
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
    exit 0
}
git -c user.email="wiki-bot@local" -c user.name="wiki-sync" commit -m "docs: sync wiki from docs/wiki"
if (-not (git remote | Select-String -Pattern "^origin$")) {
    git remote add origin $WikiRemote
}
git push -u origin HEAD:master
Pop-Location
Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
Write-Host "Wiki synced."
