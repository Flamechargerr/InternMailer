Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Users\anama\InternMailer\ ^&^& python jarvis_mode.py --start", 0, False
Set WshShell = Nothing
