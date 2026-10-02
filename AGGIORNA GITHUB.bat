@echo off
setlocal
cd /d "%~dp0"
title Aggiorna UNO Chess su GitHub

git --version >nul 2>&1
if errorlevel 1 goto git_error
git rev-parse --show-toplevel >nul 2>&1
if errorlevel 1 goto repo_error

git remote get-url origin >nul 2>&1
if errorlevel 1 goto connect_origin
goto check_history

:connect_origin
echo Collego la cartella al repository GitHub...
git remote add origin https://github.com/gianpaolodinino0-del/unochess.git
if errorlevel 1 goto remote_error

:check_history
git rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 goto sync_existing_repo
goto check_identity

:sync_existing_repo
echo Sincronizzo la cronologia iniziale con GitHub...
git fetch origin
if errorlevel 1 goto fetch_error
git show-ref --verify --quiet refs/remotes/origin/main
if errorlevel 1 goto set_main_branch
git reset --mixed origin/main
if errorlevel 1 goto sync_error

:set_main_branch
git branch -M main
if errorlevel 1 goto sync_error

:check_identity
git config user.name >nul 2>&1
if errorlevel 1 goto ask_name
git config user.email >nul 2>&1
if errorlevel 1 goto ask_email
goto stage_files

:ask_name
echo Git ha bisogno del nome da mostrare nei commit.
set /p "GIT_NAME=Nome: "
if not defined GIT_NAME goto ask_name
git config user.name "%GIT_NAME%"
if errorlevel 1 goto identity_error
goto check_identity

:ask_email
echo Inserisci l'email GitHub. Puoi usare quella noreply nelle impostazioni GitHub per non mostrare la tua email personale.
set /p "GIT_EMAIL=Email GitHub: "
if not defined GIT_EMAIL goto ask_email
git config user.email "%GIT_EMAIL%"
if errorlevel 1 goto identity_error
goto check_identity

:stage_files
echo Aggiungo le modifiche del progetto...
git add -A
if errorlevel 1 goto add_error
git diff --cached --quiet
if errorlevel 1 goto has_changes
goto no_changes

:has_changes
echo.
set "COMMIT_MESSAGE=Aggiorna UNO Chess"
set /p "COMMIT_MESSAGE=Messaggio del commit [Aggiorna UNO Chess]: "
if not defined COMMIT_MESSAGE set "COMMIT_MESSAGE=Aggiorna UNO Chess"
git commit -m "%COMMIT_MESSAGE%"
if errorlevel 1 goto commit_error

echo.
echo Invio le modifiche al branch main...
git push -u origin main
if errorlevel 1 goto push_error

echo.
echo Aggiornamento completato. Controlla Render per verificare il deploy.
pause
exit /b 0

:no_changes
echo Non ci sono modifiche da inviare.
pause
exit /b 0

:git_error
echo Git non e' installato o non e' disponibile nel PATH. Installa Git for Windows e riprova.
goto failed
:repo_error
echo Questa cartella non e' un repository Git.
goto failed
:remote_error
echo Non riesco a collegarmi al repository GitHub. Verifica URL e accesso.
goto failed
:fetch_error
echo Non riesco a scaricare la cronologia GitHub. Controlla la connessione e l'accesso.
goto failed
:sync_error
echo Sincronizzazione iniziale non riuscita. Non chiudere Git Bash: copia qui il messaggio Git.
goto failed
:identity_error
echo Non riesco a salvare nome o email per i commit.
goto failed
:add_error
echo Git non e' riuscito ad aggiungere i file.
goto failed
:commit_error
echo Il commit non e' riuscito. Controlla il messaggio Git qui sopra.
goto failed
:push_error
echo Invio non riuscito. Controlla l'accesso GitHub e il messaggio Git qui sopra.
goto failed
:failed
echo.
pause
exit /b 1
