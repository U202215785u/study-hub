$env:PYTHONPATH = "f:\360MoveData\Users\Administrator\Desktop\study web\study-hub\venv\Lib\site-packages"
$proc = Start-Process `
  -FilePath "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" `
  -ArgumentList "-u", "main.py" `
  -WorkingDirectory "f:\360MoveData\Users\Administrator\Desktop\study web\study-hub\backend" `
  -PassThru `
  -WindowStyle Normal
Write-Output "Process ID: $($proc.Id)"
