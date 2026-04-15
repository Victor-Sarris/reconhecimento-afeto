Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "start_servidor_producao.bat", 0, False
WScript.Sleep 3000 ' 
WshShell.Run "start_cliente_producao.bat", 0, False
Set WshShell = Nothing