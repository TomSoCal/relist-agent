# Update eBay Relist Agent Task Scheduler schedule
# This script must run with admin privileges

param(
    [string]$Time = "10:30",
    [string[]]$Days = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
)

$taskName = "eBayRelistAgent"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Use batch file with warning message (absolute path)
$batchFile = Join-Path $scriptDir "run_agent.bat"
$batchFile = (Resolve-Path $batchFile).Path  # Convert to absolute path

Write-Host "Using batch file: $batchFile"

# Verify batch file exists
if (-not (Test-Path $batchFile)) {
    Write-Host "ERROR: run_agent.bat not found at $batchFile"
    exit 1
}

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Error: This script requires administrator privileges."
    exit 1
}

# Convert day names to eBay day format
$dayMap = @{
    "Monday" = "MON"
    "Tuesday" = "TUE"
    "Wednesday" = "WED"
    "Thursday" = "THU"
    "Friday" = "FRI"
    "Saturday" = "SAT"
    "Sunday" = "SUN"
}

$dayOfWeek = @()
foreach ($day in $Days) {
    if ($dayMap.ContainsKey($day)) {
        $dayOfWeek += $dayMap[$day]
    }
}

# Unregister existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}

# Create new task using batch file with warning message
$action = New-ScheduledTaskAction -Execute $batchFile -WorkingDirectory $scriptDir

# Create trigger based on selected days
if ($dayOfWeek.Count -eq 7) {
    # All 7 days = daily trigger
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
} else {
    # Specific days = weekly trigger
    $trigger = New-ScheduledTaskTrigger -Weekly -At $Time -DaysOfWeek $dayOfWeek
}

$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -StartWhenAvailable

# Register with RunLevel Highest and ensure it runs hidden
$task = Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null

Write-Host "Task updated successfully!"
Write-Host "Time: $Time"
Write-Host "Days: $($Days -join ', ')"
