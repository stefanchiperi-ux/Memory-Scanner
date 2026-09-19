Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
AppPath = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = AppPath
WshShell.Run "pyw -3 """ & AppPath & "\src\app.py""", 0, False
