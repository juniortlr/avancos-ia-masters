#Requires -Version 7.0
<#
.SYNOPSIS
    Installs the Research Superpowers agent and skills for VS Code Copilot.

.DESCRIPTION
    Copies agents/ and skills/ from this repo into the two locations VS Code reads them from.
    They are different roots: the user prompts folder takes .agent.md files but does not
    support skills, and skills are read from ~/.copilot/skills.

.PARAMETER Export
    Reverse direction. Copies the installed copies back into this repo, to capture edits made
    in place. Use this before committing changes you made while working.

.EXAMPLE
    pwsh -NoProfile -File .\install.ps1
    pwsh -NoProfile -File .\install.ps1 -Export
#>
[CmdletBinding()]
param(
    [switch]$Export,
    # Agents must sit directly in the prompts folder; VS Code does not scan a nested agents\ subfolder.
    [string]$AgentTarget = (Join-Path $env:APPDATA 'Code\User\prompts'),
    [string]$SkillTarget = (Join-Path $env:USERPROFILE '.copilot\skills')
)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$repoAgents = Join-Path $repo 'agents'
$repoSkills = Join-Path $repo 'skills'

function Copy-Tree {
    param([string]$From, [string]$To, [string]$Label)

    if (-not (Test-Path $From)) { Write-Warning "missing: $From"; return }
    New-Item -ItemType Directory -Force -Path $To | Out-Null
    Copy-Item -Path (Join-Path $From '*') -Destination $To -Recurse -Force
    Write-Host ("  {0,-8} {1}" -f $Label, $To)
}

if ($Export) {
    Write-Host 'Exporting installed copies back into the repo:'
    # Only the files this repo owns — both install targets are shared with unrelated agents and skills.
    Get-ChildItem $repoAgents -Filter *.agent.md | ForEach-Object {
        $live = Join-Path $AgentTarget $_.Name
        if (Test-Path $live) { Copy-Item $live -Destination $_.FullName -Force }
        else { Write-Warning "not installed, skipped: $($_.Name)" }
    }
    Write-Host "  agents   $repoAgents"
    Get-ChildItem $repoSkills -Directory | ForEach-Object {
        $live = Join-Path $SkillTarget $_.Name
        if (Test-Path $live) { Copy-Item "$live\*" -Destination $_.FullName -Recurse -Force }
        else { Write-Warning "not installed, skipped: $($_.Name)" }
    }
    Write-Host "  skills   $repoSkills"
    Write-Host "`nReview with 'git diff' before committing."
    return
}

Write-Host 'Installing Research Superpowers:'
Copy-Tree -From $repoAgents -To $AgentTarget -Label 'agent'
Copy-Tree -From $repoSkills -To $SkillTarget -Label 'skills'

$n = (Get-ChildItem $repoSkills -Directory).Count
Write-Host "`n$n skills + 1 agent installed."
Write-Host "Open a new chat and pick 'Research Superpowers' from the agent dropdown."
Write-Host "Reload the VS Code window if it does not appear."
