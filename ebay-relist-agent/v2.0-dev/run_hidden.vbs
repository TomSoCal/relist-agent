' Run Python script completely hidden (no console window at all)
' Usage: cscript run_hidden.vbs <path_to_python_script>

If WScript.Arguments.Count < 1 Then
    WScript.Quit 1
End If

scriptPath = WScript.Arguments(0)
pythonPath = "C:\Users\tom\AppData\Local\Programs\Python\Python311\pythonw.exe"

' Create shell object
Set objShell = CreateObject("WScript.Shell")

' Run with window hidden (0 = hidden, False = don't wait)
objShell.Run pythonPath & " """ & scriptPath & """", 0, False

WScript.Quit 0
