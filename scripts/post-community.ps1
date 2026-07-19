<#
.SYNOPSIS
  Prepare / validate community announcement drafts under docs/community/.

.EXAMPLE
  .\scripts\post-community.ps1 -Check
  .\scripts\post-community.ps1 -Channel cursor-forum
  .\scripts\post-community.ps1 -Channel reddit -Open
  .\scripts\post-community.ps1 -Channel github -CreateDiscussion
#>
[CmdletBinding()]
param(
    [ValidateSet("cursor-forum", "reddit", "github", "all")]
    [string]$Channel = "cursor-forum",
    [switch]$Open,
    [switch]$CreateDiscussion,
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Helper = Join-Path $PSScriptRoot "community_drafts.py"
$env:PYTHONPATH = (Join-Path $RepoRoot "src") + [IO.Path]::PathSeparator + $RepoRoot

function Invoke-Helper {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PyArgs)
    $prev = Get-Location
    try {
        Set-Location $RepoRoot
        & python $Helper @PyArgs
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally {
        Set-Location $prev
    }
}

if ($Check) {
    Write-Host "Checking community drafts..."
    Invoke-Helper check
    Write-Host "OK - drafts match pyproject version and tool inventory."
    exit 0
}

if ($CreateDiscussion) {
    if ($Channel -ne "github" -and $Channel -ne "all") {
        Write-Host "-CreateDiscussion only applies to -Channel github (or all)."
    }
    Write-Host "Creating GitHub Discussion from github draft..."
    Push-Location $RepoRoot
    try {
        $url = & python $Helper create-discussion
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Host "Created: $url"
    }
    finally {
        Pop-Location
    }
    if ($Channel -eq "github") { exit 0 }
}

$channels = if ($Channel -eq "all") {
    @("cursor-forum", "reddit", "github")
} else {
    @($Channel)
}

Push-Location $RepoRoot
try {
    foreach ($ch in $channels) {
        $json = & python $Helper show --channel $ch
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $info = $json | ConvertFrom-Json
        Write-Host ""
        Write-Host "=== $($info.channel) ($($info.path)) ==="
        Write-Host "Title: $($info.title)"
        Write-Host "Version: $($info.version)  Tools: $($info.tools)"
        Write-Host ""

        $clip = "Title: $($info.title)`r`n`r`n$($info.body)"
        try {
            Set-Clipboard -Value $clip
            Write-Host "Copied title+body to clipboard."
        }
        catch {
            Write-Host "Clipboard unavailable: $_"
            Write-Host "---- BODY ----"
            Write-Host $info.body
            Write-Host "--------------"
        }

        if ($Open -and $info.url) {
            Write-Host "Opening $($info.url)"
            Start-Process $info.url
        }
        else {
            Write-Host "Next: paste clipboard into the compose UI ($($info.url))"
        }
    }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Done."
