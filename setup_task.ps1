$action = New-ScheduledTaskAction -Execute 'C:\Users\mingj\AppData\Local\Programs\Python\Python312-arm64\python.exe' -Argument '"C:\Data\job alert robot\extracted\job_alert_bot\main.py"' -WorkingDirectory 'C:\Data\job alert robot\extracted\job_alert_bot'
$trigger = New-ScheduledTaskTrigger -Daily -At 10am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'AI Job Alert Bot' -Action $action -Trigger $trigger -Settings $settings -Description 'Daily AI job alert email' -Force
