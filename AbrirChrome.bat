@echo off
set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

start "" %CHROME% --remote-debugging-port=9222 --user-data-dir="%~dp0chrome-profile" "https://www.nfse.gov.br/EmissorNacional/"

echo Chrome aberto. Faca login no nfse.gov.br nessa janela.
echo Depois de logar, pode rodar o EmitirNFSe.exe.
pause
