# Puts the built host mod into lab\payload and, when the payload is installed, syncs it into Trepang2's Win64 folder:
#   ue4ss\UE4SS.dll                        <- our UE4SS build (the mod links against it)
#   ue4ss\Mods\T2Passthrough\dlls\main.dll <- the host mod (+ enabled in mods.txt)
#   reshade-shaders\Shaders\MCPassthrough.fx, ReShadePreset.ini with the MCPassthrough technique on
# Every deployed build is kept in lab\builds\<time> (crash_check.py symbolizes a crash with the DLL that crashed).
$ErrorActionPreference = 'Stop'
$root    = Split-Path $PSScriptRoot -Parent
$payload = Join-Path $root 'lab\payload'
$bin     = Join-Path $root 'src\build'
$win64   = 'C:\Program Files (x86)\Steam\steamapps\common\Trepang2\CPPFPS\Binaries\Win64'

if (Get-Process CPPFPS-Win64-Shipping -ErrorAction SilentlyContinue) { throw 'Trepang2 is running: close it first.' }

Copy-Item (Join-Path $bin 'Game__Shipping__Win64\bin\UE4SS.dll'), (Join-Path $bin 'Game__Shipping__Win64\bin\UE4SS.pdb') (Join-Path $payload 'ue4ss') -Force
$mod = Join-Path $payload 'ue4ss\Mods\T2Passthrough\dlls'
New-Item -ItemType Directory -Force $mod | Out-Null
Copy-Item (Join-Path $bin 't2-host\T2Passthrough.dll') (Join-Path $mod 'main.dll') -Force
if (Test-Path (Join-Path $bin 't2-host\T2Passthrough.pdb')) { Copy-Item (Join-Path $bin 't2-host\T2Passthrough.pdb') (Join-Path $mod 'main.pdb') -Force }
$arch = Join-Path $root ('lab\builds\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force $arch | Out-Null
Copy-Item (Join-Path $bin 't2-host\T2Passthrough.dll'), (Join-Path $bin 't2-host\T2Passthrough.pdb'), (Join-Path $bin 'Game__Shipping__Win64\bin\UE4SS.dll') $arch -ErrorAction SilentlyContinue

$modsTxt = Join-Path $payload 'ue4ss\Mods\mods.txt'
$lines = Get-Content $modsTxt
if (-not ($lines -match '^T2Passthrough')) {
    $at = [Array]::IndexOf($lines, ($lines -match '^T2Probe')[0]) + 1
    $lines = $lines[0..($at - 1)] + 'T2Passthrough : 1' + $lines[$at..($lines.Count - 1)]
    Set-Content $modsTxt $lines -Encoding ascii
}

Copy-Item (Join-Path $root 'src\t2-host\shaders\MCPassthrough.fx') (Join-Path $payload 'reshade-shaders\Shaders') -Force

if (Test-Path (Join-Path $win64 'ue4ss')) {
    foreach ($rel in 'ue4ss\UE4SS.dll', 'ue4ss\UE4SS.pdb', 'ue4ss\Mods\mods.txt', 'ue4ss\Mods\T2Passthrough', 'reshade-shaders\Shaders\MCPassthrough.fx', 'ReShadePreset.ini') {
        Copy-Item (Join-Path $payload $rel) (Split-Path (Join-Path $win64 $rel) -Parent) -Recurse -Force
        "  synced $rel"
    }
} else {
    'payload not installed in Win64: run lab\install.ps1'
}
