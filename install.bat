@echo off
rem Installs the mods in mods\recommended.txt into Hammerting. Close the game first.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 tools\hmod.py install recommended) else (python tools\hmod.py install recommended)
echo.
echo If it says "installed", set Hammerting's Steam Launch Options to:
echo %%command%% --game-extra-archives danger_zone/hammerting_mods.wkz
pause
