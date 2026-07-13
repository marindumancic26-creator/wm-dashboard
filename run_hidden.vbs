' Generic invisible launcher for PowerShell scripts.
' Usage: wscript.exe //B run_hidden.vbs "<script.ps1>"
' WScript.Shell.Run with WindowStyle=0 never allocates a console window,
' unlike "powershell -WindowStyle Hidden" which can still flash briefly.

Set objShell = CreateObject("WScript.Shell")

scriptPath = WScript.Arguments(0)
command = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File """ & scriptPath & """"

objShell.Run command, 0, False
