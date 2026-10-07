# Foreground window helper, so launching Trepang2 doesn't keep the user's focus:
#   fg.ps1 save            prints the current foreground window handle
#   fg.ps1 restore <hwnd>  brings that window back to the front (Alt tap lifts Windows' foreground lock)
param([string]$Cmd = 'save', [long]$Hwnd = 0)
Add-Type @'
using System; using System.Runtime.InteropServices;
public static class FG {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, IntPtr e);
}
'@
if ($Cmd -eq 'save') { [long][FG]::GetForegroundWindow(); return }
$h = [IntPtr]$Hwnd
if (-not [FG]::IsWindow($h)) { 'gone'; return }
for ($i = 0; $i -lt 5 -and [FG]::GetForegroundWindow() -ne $h; $i++) {
    [FG]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [FG]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)
    [FG]::SetForegroundWindow($h) | Out-Null
    Start-Sleep -Milliseconds 150
}
if ([FG]::GetForegroundWindow() -eq $h) { 'restored' } else { 'not restored' }
