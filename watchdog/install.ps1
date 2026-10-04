$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -Verb runAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "Installing Epson Watchdog..."

wevtutil sl Microsoft-Windows-PrintService/Operational /e:true

$TaskName = "EpsonSpoolerWatchdog"
$TaskPath = "C:\ProgramData\EpsonSpoolerWatchdog\watchdog.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$TaskPath`""
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit 0
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Restart_Print_Spooler.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-WindowStyle Hidden -Command `"Start-Process cmd -ArgumentList '/c net stop spooler & net start spooler & timeout /t 2' -Verb RunAs`""
$Shortcut.IconLocation = "shell32.dll, 238"
$Shortcut.Save()

$ShortcutDiag = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Diagnostics_Printer.lnk")
$ShortcutDiag.TargetPath = "powershell.exe"
$ShortcutDiag.Arguments = "-ExecutionPolicy Bypass -File `"C:\ProgramData\EpsonSpoolerWatchdog\diagnose.ps1`""
$ShortcutDiag.IconLocation = "shell32.dll, 22"
$ShortcutDiag.Save()

Start-ScheduledTask -TaskName $TaskName

Write-Host "Installed Successfully!"
Start-Sleep -Seconds 3
