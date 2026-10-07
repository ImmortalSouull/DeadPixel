# Posts a key press (WM_KEYDOWN + WM_KEYUP) straight to Trepang2's window, without bringing it to the front: the
# "PRESS ANY KEY" title screen takes it even while another app has the focus (nothing reaches other windows).
#   t2-postkey.ps1 [vk = 0x0D]
param([int]$Vk = 0x0D)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class P {
  [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern uint MapVirtualKeyW(uint c, uint t);
}
'@
$p = Get-Process CPPFPS-Win64-Shipping -ErrorAction SilentlyContinue | Where-Object MainWindowHandle -ne 0 | Select-Object -First 1
if (-not $p) { throw 'no Trepang2 window' }
$scan = [P]::MapVirtualKeyW([uint32]$Vk, 0)
$down = [IntPtr](1 -bor ($scan -shl 16))
$up = [IntPtr]([int64]1 -bor ([int64]$scan -shl 16) -bor (3L -shl 30))
[P]::PostMessageW($p.MainWindowHandle, 0x0100, [IntPtr]$Vk, $down) | Out-Null
Start-Sleep -Milliseconds 60
[P]::PostMessageW($p.MainWindowHandle, 0x0101, [IntPtr]$Vk, $up) | Out-Null
"posted key $Vk"
