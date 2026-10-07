# Moves the Trepang2 window to the laptop screen (1920x1200 at 3440,667), as for RoN: the game follows with a
# 1920x1200 backbuffer in windowed fullscreen. Prints the client size afterwards.
$ErrorActionPreference = 'Stop'
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class R {
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public struct RECT { public int L, T, R, B; }
}
'@
[R]::SetProcessDPIAware() | Out-Null
$p = Get-Process CPPFPS-Win64-Shipping | Where-Object MainWindowHandle -ne 0 | Select-Object -First 1
if (-not $p) { throw 'Trepang2 is not running' }
$rc0 = New-Object R+RECT
[R]::GetClientRect($p.MainWindowHandle, [ref]$rc0) | Out-Null
if (($rc0.R - $rc0.L) -ne 1920 -or ($rc0.B - $rc0.T) -ne 1200) { [R]::SetWindowPos($p.MainWindowHandle, [IntPtr]::Zero, 3440, 667, 1920, 1200, 0x0014) | Out-Null }
Start-Sleep -Seconds 4
$rc = New-Object R+RECT
[R]::GetClientRect($p.MainWindowHandle, [ref]$rc) | Out-Null
"client $($rc.R - $rc.L)x$($rc.B - $rc.T)"
