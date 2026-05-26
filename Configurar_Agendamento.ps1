# =========================================================
# Mosaic RDE RPA - Configurador de Agendamento
# Execute com: clique direito > 'Executar com PowerShell'
# (Administrador necessario para registrar as tarefas)
# =========================================================

$Exe     = 'C:\Users\esantan3\AppData\Local\Programs\Python\Python314\python.exe'
$ArgA    = '"c:\Users\esantan3\OneDrive - The Mosaic Company\Área de Trabalho\Projetos\Automação\OCR Report Atlas\Complete_Edition.py" --auto-atlas'
$ArgS    = '"c:\Users\esantan3\OneDrive - The Mosaic Company\Área de Trabalho\Projetos\Automação\OCR Report Atlas\Complete_Edition.py" --auto-sap'
$WorkDir = 'c:\Users\esantan3\OneDrive - The Mosaic Company\Área de Trabalho\Projetos\Automação\OCR Report Atlas'

if (-not (Test-Path $Exe)) { Write-Host 'ERRO: Python nao encontrado.' -ForegroundColor Red; pause; exit 1 }

# --- TAREFA 1: Atlas Diario (Seg-Sex 07:30) ---
$a1 = New-ScheduledTaskAction -Execute $Exe -Argument $ArgA -WorkingDirectory $WorkDir
$t1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '07:30'
$s1 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName 'Mosaic RPA - Atlas Diario' -Action $a1 -Trigger $t1 -Settings $s1 -Force | Out-Null
Write-Host '  [OK] Atlas Diario : Seg-Sex as 07:30' -ForegroundColor Green

# --- TAREFA 2: SAP a cada 2h (inicio 16:18) ---
$a2 = New-ScheduledTaskAction -Execute $Exe -Argument $ArgS -WorkingDirectory $WorkDir
$t2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '16:18'
$rep = New-ScheduledTaskTrigger -Once -At '16:18' -RepetitionInterval (New-TimeSpan -Hours 2) -RepetitionDuration (New-TimeSpan -Hours 4)
$t2.Repetition = $rep.Repetition
$s2 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName 'Mosaic RPA - SAP 2h' -Action $a2 -Trigger $t2 -Settings $s2 -Force | Out-Null
Write-Host '  [OK] SAP a cada 2h : Seg-Sex, 16:18 ate 20:00' -ForegroundColor Green

Write-Host ''
Write-Host 'Agendamento configurado com sucesso!' -ForegroundColor Cyan
pause