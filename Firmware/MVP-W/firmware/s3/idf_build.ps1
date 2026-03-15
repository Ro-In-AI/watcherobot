$env:MSYSTEM = ""
$env:MSYS = ""
& "C:\Espressif\frameworks\esp-idf-v5.2.1\export.ps1"
idf.py $args
