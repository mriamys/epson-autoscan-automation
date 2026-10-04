$LogFile = "C:\ProgramData\EpsonSpoolerWatchdog\watchdog.log"
$PrinterName = "L3350 Series(Сеть)"
$CooldownSeconds = 60

Function Write-Log($Message) {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $Line
    Write-Output $Line
}

Function Restart-Spooler {
    Write-Log "Restarting Print Spooler..."
    Stop-Service -Name Spooler -Force
    Start-Service -Name Spooler
    Write-Log "Print Spooler restarted successfully."
}

Write-Log "Watchdog started."

$LastRestartTime = [DateTime]::MinValue
$LastJobId = -1
$JobStuckCount = 0

while ($true) {
    Start-Sleep -Seconds 10
    
    $Now = Get-Date
    if (($Now - $LastRestartTime).TotalSeconds -lt $CooldownSeconds) {
        continue
    }

    $NeedsRestart = $false

    # 1. Проверка статуса службы Spooler
    $Spooler = Get-Service -Name Spooler -ErrorAction SilentlyContinue
    if ($Spooler -and $Spooler.Status -ne 'Running') {
        Write-Log "Detected Spooler service is not running."
        $NeedsRestart = $true
    }

    # 2. Проверка Event 842 / 0x80004005
    if (-not $NeedsRestart) {
        $Events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PrintService/Operational'; ID=842; StartTime=(Get-Date).AddSeconds(-15)} -ErrorAction SilentlyContinue
        if ($Events) {
            foreach ($Event in $Events) {
                if ($Event.Message -match "0x80004005") {
                    Write-Log "Detected PrintService Event 842 / 0x80004005."
                    $NeedsRestart = $true
                    break
                }
            }
        }
    }

    # 3. Проверка зависших заданий
    if (-not $NeedsRestart) {
        $Jobs = Get-PrintJob -PrinterName $PrinterName -ErrorAction SilentlyContinue
        if ($Jobs) {
            $CurrentJob = $Jobs[0]
            if ($CurrentJob.Id -eq $LastJobId) {
                $JobStuckCount++
                if ($JobStuckCount -ge 4) { # 4 итерации по 10 сек = 40 секунд задание висит
                    Write-Log "Detected stuck print job ID $($CurrentJob.Id) for $PrinterName (stuck for 40s)."
                    $NeedsRestart = $true
                    $JobStuckCount = 0
                }
            } else {
                $LastJobId = $CurrentJob.Id
                $JobStuckCount = 0
            }
        } else {
            $LastJobId = -1
            $JobStuckCount = 0
        }
    }

    if ($NeedsRestart) {
        Restart-Spooler
        $LastRestartTime = Get-Date
        $LastJobId = -1
        $JobStuckCount = 0
    }
}
