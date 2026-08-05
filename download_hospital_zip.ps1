$url = 'https://qnkidasiemptwakjzwev.supabase.co/storage/v1/object/public/modules/hospital_management.zip?'
$outFile = Join-Path (Get-Location) 'hospital_management.zip'
Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing
Write-Host "Downloaded $outFile"
