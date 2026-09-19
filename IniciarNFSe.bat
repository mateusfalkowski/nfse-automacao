@echo off
setlocal
cd /d "%~dp0"

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
