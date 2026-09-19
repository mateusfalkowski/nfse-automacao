@echo off
setlocal
cd /d "%~dp0"

if not exist "EmitirNFSe.exe" (
    echo Primeira vez rodando aqui: extraindo arquivos, aguarde alguns segundos...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$self = '%~f0'; $dir = '%~dp0'; $lines = [IO.File]::ReadAllLines($self); $idx = [Array]::IndexOf($lines, '::PAYLOAD_BASE64_START::'); $b64 = [string]::Join('', $lines[($idx+1)..($lines.Count-1)]); $bytes = [Convert]::FromBase64String($b64); $zipPath = Join-Path $dir '_payload.zip'; [IO.File]::WriteAllBytes($zipPath, $bytes); Expand-Archive -LiteralPath $zipPath -DestinationPath $dir -Force; Remove-Item $zipPath"
    if not exist "EmitirNFSe.exe" (
        echo ERRO: nao consegui extrair os arquivos. Fale com o Mateus.
        pause
        exit /b 1
    )
)

echo ============================================
echo   NFS-e Automation
echo ============================================
echo.

set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

echo Abrindo o Chrome...
start "" %CHROME% --remote-debugging-port=9222 --user-data-dir="%~dp0chrome-profile" "https://www.nfse.gov.br/EmissorNacional/"

echo.
echo Faca login no nfse.gov.br na janela do Chrome que abriu.
echo Quando terminar de logar, volte aqui e aperte uma tecla para continuar.
pause

echo.
echo Rodando o EmitirNFSe...
echo.
"%~dp0EmitirNFSe.exe"

echo.
pause
exit /b
::PAYLOAD_BASE64_START::
