@echo off
rem Launched by lab.wsb LogonCommand. Runs setup.ps1 headless (the Sandbox has no
rem reliable visible console at logon). Watch progress on the HOST instead:
rem   C:\dac-lab\out\setup.log          (live)
rem   C:\dac-lab\out\SETUP-COMPLETE.txt (done)  /  SETUP-FAILED.txt (error)
rem iex on the script text avoids the Sandbox's .ps1 execution-policy block.
powershell.exe -NoProfile -Command "iex (Get-Content 'C:\lab\scripts\setup.ps1' -Raw)"
