# Run once as Administrator to register the 12pm daily Task Scheduler job.
$taskName  = "eBayRelistAgent"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = (Get-Command python).Source
$script    = Join-Path $scriptDir "ebay_relist_agent.py"

$action   = New-ScheduledTaskAction -Execute $pythonExe -Argument $script -WorkingDirectory $scriptDir
$trigger  = New-ScheduledTaskTrigger -Daily -At "10:30AM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
Write-Host "Task '$taskName' registered - runs daily at 10:30 AM."
