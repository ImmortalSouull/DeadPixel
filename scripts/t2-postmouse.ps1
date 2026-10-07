# Posts a mouse button click straight to Trepang2's window (no focus, cursor untouched): left|right [hold ms]
param([string]$Button = 'left', [int]$Hold = 80)
$ErrorActionPreference = 'Stop'
Add-Type 'using System; using System.Runtime.InteropServices; public static class PM { [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l); }'
$p = Get-Process CPPFPS-Win64-Shipping -ErrorAction SilentlyContinue | Where-Object MainWindowHandle -ne 0 | Select-Object -First 1
if (-not $p) { throw 'no Trepang2 window' }
$down, $up, $mk = if ($Button -eq 'right') { 0x0204, 0x0205, 2 } else { 0x0201, 0x0202, 1 }
$center = [IntPtr]((600 -shl 16) -bor 960)
[PM]::PostMessageW($p.MainWindowHandle, $down, [IntPtr]$mk, $center) | Out-Null
Start-Sleep -Milliseconds $Hold
[PM]::PostMessageW($p.MainWindowHandle, $up, [IntPtr]0, $center) | Out-Null
"posted $Button click"
