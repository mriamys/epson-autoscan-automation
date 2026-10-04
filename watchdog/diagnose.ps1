Write-Host "=== SPOOLER SERVICE STATUS ===" -ForegroundColor Cyan
Get-Service Spooler | Format-List Name, Status, StartType

Write-Host "`n=== PRINTER L3350 Series(Сеть) STATUS ===" -ForegroundColor Cyan
Get-Printer -Name "L3350 Series(Сеть)" -ErrorAction SilentlyContinue | Format-List Name, PrinterStatus, PortName, DriverName, JobCount

Write-Host "`n=== CURRENT PRINT JOBS ===" -ForegroundColor Cyan
Get-PrintJob -PrinterName "L3350 Series(Сеть)" -ErrorAction SilentlyContinue | Format-Table -AutoSize

Write-Host "`n=== RECENT PrintService EVENTS (Errors and 842) ===" -ForegroundColor Cyan
try {
    Get-WinEvent -LogName "Microsoft-Windows-PrintService/Operational" -MaxEvents 30 -ErrorAction Stop |
        Where-Object { $_.Id -in 842,800,801,805 } |
        Select-Object TimeCreated, Id, Message | Format-Table -Wrap -AutoSize
} catch {
    Write-Host "Log Microsoft-Windows-PrintService/Operational is empty, disabled, or access denied." -ForegroundColor Red
    Write-Host "Please run as Administrator." -ForegroundColor Yellow
}

Write-Host "`nPress any key to exit..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
