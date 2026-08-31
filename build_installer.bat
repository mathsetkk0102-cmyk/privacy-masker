@echo off
setlocal EnableExtensions

cd /d "%~dp0"
chcp 65001 >nul

echo [PrivacyMasker] Installer build script
echo.

if not exist main.py (
    echo [ERROR] main.py was not found. Run this script from the privacy_masker project folder.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv Python was not found.
    echo Run build_windows.bat first, then run build_installer.bat again.
    pause
    exit /b 1
)

if not exist "dist\PrivacyMasker\PrivacyMasker.exe" (
    echo [ERROR] dist\PrivacyMasker\PrivacyMasker.exe was not found.
    echo Run build_windows.bat first, then run build_installer.bat again.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" "tools\build_installer.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed.
    pause
    exit /b 1
)

echo.
echo Installer created:
echo dist\PrivacyMaskerSetup.exe
echo.
pause
exit /b 0
