Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName System.Windows.Forms

$text = "PiWin pilot OK - " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Start-Process notepad.exe
Start-Sleep -Seconds 2

SendKeys -Keys $text
Start-Sleep -Seconds 1
Write-Host "PASS: text typed into Notepad. Closing without saving."
Get-Process notepad -ErrorAction SilentlyContinue | ForEach-Object {
    $_.CloseMainWindow() | Out-Null
    Start-Sleep -Milliseconds 500
    if (-not $_.HasExited) {
        [System.Windows.Forms.SendKeys]::SendWait("%n")
        $_.CloseMainWindow() | Out-Null
    }
}
Write-Host "Done."
