# Gera o instalador de arquivo unico "EmitirNFSe.bat": um .bat que carrega o
# EmitirNFSe.exe, o LEIA-ME.txt e o config/settings.example.yaml embutidos
# (codificados em base64) e se auto-extrai na primeira vez que roda.
#
# Pre-requisito: já ter gerado dist\EmitirNFSe.exe (veja o comando pyinstaller
# no README, secao "Gerar um .exe").
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File build_installer.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$exePath = Join-Path $root "dist\EmitirNFSe.exe"
if (-not (Test-Path $exePath)) {
    throw "dist\EmitirNFSe.exe nao encontrado. Rode o pyinstaller primeiro (veja o README)."
}

$payloadDir = Join-Path $root "_installer_payload"
Remove-Item $payloadDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $payloadDir "config") | Out-Null

Copy-Item $exePath (Join-Path $payloadDir "EmitirNFSe.exe")
Copy-Item (Join-Path $root "LEIA-ME.txt") (Join-Path $payloadDir "LEIA-ME.txt")
Copy-Item (Join-Path $root "config\settings.example.yaml") (Join-Path $payloadDir "config\settings.example.yaml")

$zipPath = Join-Path $root "_installer_payload.zip"
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $payloadDir "*") -DestinationPath $zipPath

# Embute o zip como base64 (texto puro) — bytes binarios "crus" colados direto
# no .bat quebram o parser do cmd.exe mesmo depois de um "exit /b" (ele tenta
# ler o arquivo inteiro e trava em bytes NUL). Base64 nao tem esse problema.
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($zipPath))
$lineLen = 200
$sb = New-Object System.Text.StringBuilder
for ($i = 0; $i -lt $b64.Length; $i += $lineLen) {
    $len = [Math]::Min($lineLen, $b64.Length - $i)
    [void]$sb.AppendLine($b64.Substring($i, $len))
}

$stub = [IO.File]::ReadAllText((Join-Path $root "installer_stub.bat"))
$outPath = Join-Path $root "EmitirNFSe.bat"
[IO.File]::WriteAllText($outPath, ($stub + $sb.ToString()), [Text.Encoding]::ASCII)

Remove-Item $payloadDir -Recurse -Force
Remove-Item $zipPath -Force

$size = (Get-Item $outPath).Length
Write-Host "Gerado: $outPath ($size bytes)"
