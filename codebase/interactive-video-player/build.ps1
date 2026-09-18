$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force build | Out-Null
$assets = Join-Path $PSScriptRoot "assets"
$entry = Join-Path $PSScriptRoot "main.py"
python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name interactive-recap `
  --specpath build `
  --workpath build\work `
  --distpath dist `
  --add-data "$assets;assets" `
  $entry

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$artifact = Join-Path $PSScriptRoot "dist\interactive-recap.exe"
if (-not (Test-Path -LiteralPath $artifact)) {
  throw "Build finished without producing $artifact"
}
Write-Host "Built: $artifact"
