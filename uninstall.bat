@echo off
rem Removes the mods and restores the original game DLLs. Close the game first.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 tools\hmod.py uninstall) else (python tools\hmod.py uninstall)
echo.
echo Now clear Hammerting's Steam Launch Options.
pause
