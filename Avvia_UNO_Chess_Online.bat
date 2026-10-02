@echo off
setlocal
cd /d "%~dp0"
title UNO Chess Online - Avvio

echo ========================================
echo       UNO Chess Online - avvio
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creo l'ambiente Python del gioco...
    py -3 -m venv .venv
    if errorlevel 1 goto python_error
)

echo Controllo e installo le dipendenze...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error

echo.
echo Indirizzi IPv4 di questo PC:
ipconfig | findstr /i "IPv4"
echo.
echo Avvio il server web. Lascia aperta la finestra del server.
start "UNO Chess Online - server" "%CD%\.venv\Scripts\python.exe" "%CD%\webapp.py"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5000"

echo Si e' aperto il gioco sul PC.
echo Per il telefono sulla stessa Wi-Fi, usa l'indirizzo IPv4 mostrato sopra
echo seguito da :5000, per esempio http://192.168.1.25:5000
echo Se Windows chiede l'accesso alla rete, consenti l'accesso sulle reti private.
echo.
echo Questa finestra puo' essere chiusa. Per fermare il server, chiudi la finestra
echo "UNO Chess Online - server".
pause
exit /b 0

:python_error
echo.
echo Non trovo Python 3. Installa Python da python.org selezionando "Add Python to PATH",
echo poi esegui di nuovo questo file.
pause
exit /b 1

:install_error
echo.
echo Installazione non riuscita. Controlla la connessione Internet e riprova.
pause
exit /b 1
