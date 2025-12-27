
$env:OPENAI_API_KEY=ADD_YOUR_OWN_KEY_HERE

Write-Host "Building Docker Image..." -ForegroundColor Cyan
docker build -t pharmacy-bot .

Write-Host "Starting Pharmacy Bot..." -ForegroundColor Green
docker run -p 8501:8501 `
  --dns 8.8.8.8 `
  -e OPENAI_API_KEY=$env:OPENAI_API_KEY `
  -v "${PWD}/data:/app/data" `
  pharmacy-bot