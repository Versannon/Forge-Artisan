<#
.SYNOPSIS
    ForgeArtisan Windows Installer Script with PATH Configuration
.DESCRIPTION
    Installs ForgeArtisan executable and assets, prompts to add ForgeArtisan to the user's system PATH,
    and sets up Desktop and Start Menu shortcuts.
#>

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\ForgeArtisan",
    [switch]$AddToPath = $true,
    [switch]$Silent = $false
)

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         ForgeArtisan 3D Artist Engine Installer          " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Version: 1.0.0 (Meta Muse Spark • SAM 3.1 • Unity Bridge)"
Write-Host ""

$sourceDir = Split-Path -Parent $PSScriptRoot
if (!(Test-Path "$sourceDir\cli.py")) {
    $sourceDir = $PSScriptRoot
}

# 1. Confirm Installation Path
if (!$Silent) {
    Write-Host "Default destination: $InstallPath" -ForegroundColor Gray
    $customPath = Read-Host "Press ENTER to accept default path (or type a custom path)"
    if (![string]::IsNullOrWhiteSpace($customPath) -and $customPath.Trim().ToUpper() -ne "Y" -and $customPath.Trim().ToUpper() -ne "YES") {
        $InstallPath = $customPath.Trim()
    }
}

Write-Host "`n📁 Installing ForgeArtisan to: $InstallPath" -ForegroundColor Green
if (!(Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# 2. Copy application files / binaries
Write-Host "📦 Copying binaries and packages..." -ForegroundColor Gray
$distExeDir = "$sourceDir\dist\forge-artisan"
if (Test-Path "$distExeDir\forge-artisan.exe") {
    Write-Host "   -> Bundling standalone compiled binary forge-artisan.exe" -ForegroundColor Green
    & robocopy "$distExeDir" "$InstallPath" /E /MT:8 /R:1 /W:1 /NFL /NDL /NP /NJH /NJS | Out-Null
} else {
    & robocopy "$sourceDir" "$InstallPath" /E /XD "dist" "build" ".venv" /MT:8 /R:1 /W:1 /NFL /NDL /NP /NJH /NJS | Out-Null
}

# 3. Create launcher wrappers: forge-artisan.bat
$batWrapper = @"
@echo off
set "PYTHONUTF8=1"
if exist "%~dp0forge-artisan.exe" (
    "%~dp0forge-artisan.exe" %*
) else (
    python "%~dp0cli.py" %*
)
"@
Set-Content -Path "$InstallPath\forge-artisan.bat" -Value $batWrapper -Force
Set-Content -Path "$InstallPath\forge-artisan.cmd" -Value $batWrapper -Force

# 4. PATH Adding Option
$addPathChoice = "Y"
if (!$Silent) {
    Write-Host ""
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host " PATH CONFIGURATION (Recommended):" -ForegroundColor Yellow
    Write-Host " Adding ForgeArtisan to PATH enables running 'forge-artisan' "
    Write-Host " directly from PowerShell, CMD, or any terminal window."
    Write-Host "----------------------------------------------------------" -ForegroundColor DarkCyan
    $resp = Read-Host "Add ForgeArtisan to user PATH environment variable? (Y/N) [Default: Y]"
    if (![string]::IsNullOrWhiteSpace($resp)) {
        $addPathChoice = $resp.Trim().ToUpper()
    }
}

if ($addPathChoice -eq "Y" -or $addPathChoice -eq "YES") {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if ($currentPath -notlike "*$InstallPath*") {
        $newPath = "$currentPath;$InstallPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::User)
        $env:Path = "$env:Path;$InstallPath"
        Write-Host "✅ Added $InstallPath to User PATH." -ForegroundColor Green
        Write-Host "   (Note: Existing open terminal windows must be restarted to inherit the new PATH)." -ForegroundColor Yellow
    } else {
        Write-Host "ℹ️  ForgeArtisan is already in your PATH." -ForegroundColor Gray
    }
} else {
    Write-Host "⏭️  Skipped PATH modification." -ForegroundColor DarkGray
}

# 5. Create Desktop Shortcut for Web UI
try {
    $wsh = New-Object -ComObject WScript.Shell
    $desktopPaths = @(
        "$([Environment]::GetFolderPath('Desktop'))",
        "$env:USERPROFILE\OneDrive\Desktop",
        "$env:USERPROFILE\Desktop"
    )
    foreach ($dp in $desktopPaths) {
        if (Test-Path $dp) {
            $shortcutPath = Join-Path $dp "ForgeArtisan Studio.lnk"
            $shortcut = $wsh.CreateShortcut($shortcutPath)
            if (Test-Path "$InstallPath\forge-artisan.exe") {
                $shortcut.TargetPath = "$InstallPath\forge-artisan.exe"
                $shortcut.Arguments = "ui"
            } else {
                $shortcut.TargetPath = "cmd.exe"
                $shortcut.Arguments = "/k `"$InstallPath\forge-artisan.bat`" ui"
            }
            $shortcut.WorkingDirectory = $InstallPath
            $shortcut.Description = "Launch ForgeArtisan 3D Technical Artist Web Studio"
            $shortcut.Save()
            Write-Host "🖥️  Updated Desktop shortcut: '$shortcutPath'" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "⚠️  Could not create desktop shortcut: $_" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "               Installation Completed!                    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Quick Start Commands:" -ForegroundColor Yellow
Write-Host "  1. Test Status:           forge-artisan status"
Write-Host "  2. Launch Web UI:         forge-artisan ui"
Write-Host "  3. Autonomous Craft Run:  forge-artisan run `"vintage steam locomotive`""
Write-Host "  4. Install Unity Bridge:  forge-artisan install-unity-bridge <Path-To-Unity-Project>"
Write-Host "  5. Launch MCP Server:     forge-artisan mcp"
Write-Host "==========================================================" -ForegroundColor Cyan

if (!$Silent) {
    Write-Host "`nPress any key to exit installer..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
