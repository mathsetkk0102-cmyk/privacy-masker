@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
chcp 65001 >nul

if not exist build_logs mkdir build_logs
call :make_timestamp
set "BUILD_LOG=build_logs\build_%BUILD_TIMESTAMP%.log"
set "FAILED_STAGE=initialization"
set "PYTHON_CMD="
set "PYTHON_VERSION=unknown"
set "PIP_VERSION=unknown"
set "PYINSTALLER_VERSION=unknown"
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "USER_PYTHON_EXE=%PYTHON_EXE%"

call :log ""
call :log "[PrivacyMasker] Windows build script"
call :log "Log file: %BUILD_LOG%"
call :log ""

call :check_project_root || goto build_failed
call :find_python || goto build_failed
call :create_or_use_venv || goto build_failed
call :upgrade_pip || goto build_failed
call :install_requirements || goto build_failed
call :ensure_pyinstaller || goto build_failed
call :run_tests || goto build_failed
call :clean_build_dirs || goto build_failed
call :run_pyinstaller || goto build_failed
call :check_exe || goto build_failed

call :log ""
call :log "[SUCCESS] Build completed."
call :log "Executable: %CD%\dist\PrivacyMasker\PrivacyMasker.exe"
call :log "Log file: %CD%\%BUILD_LOG%"
call :log ""
pause
exit /b 0

:make_timestamp
set "BUILD_TIMESTAMP="
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss" 2^>nul') do set "BUILD_TIMESTAMP=%%I"
if defined BUILD_TIMESTAMP exit /b 0
set "BUILD_TIMESTAMP=%DATE%_%TIME%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP:/=%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP:-=%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP:.=%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP::=%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP: =_%"
set "BUILD_TIMESTAMP=%BUILD_TIMESTAMP%_%RANDOM%"
exit /b 0

:check_project_root
set "FAILED_STAGE=project root check"
call :log "[0/9] Checking project root..."
if not exist main.py (
    call :log "[ERROR] main.py was not found. Run this script from the privacy_masker project folder."
    exit /b 1
)
if not exist privacy_masker.spec (
    call :log "[ERROR] privacy_masker.spec was not found. Run this script from the privacy_masker project folder."
    exit /b 1
)
if not exist requirements.txt (
    call :log "[ERROR] requirements.txt was not found. Run this script from the privacy_masker project folder."
    exit /b 1
)
call :log "Project root OK: %CD%"
exit /b 0

:find_python
set "FAILED_STAGE=python discovery"
call :log "[1/9] Finding Python launcher..."
if defined USER_PYTHON_EXE (
    call :log "Trying user-provided PYTHON_EXE: %USER_PYTHON_EXE%"
    call :try_python "%USER_PYTHON_EXE%"
    if defined PYTHON_CMD exit /b 0
)
call :try_python py -3
if defined PYTHON_CMD exit /b 0
call :try_python py
if defined PYTHON_CMD exit /b 0
call :try_python python
if defined PYTHON_CMD exit /b 0
call :try_python python3
if defined PYTHON_CMD exit /b 0
call :try_common_python_paths
if defined PYTHON_CMD exit /b 0

call :log ""
call :log "[ERROR] Python could not be found or pip is not available."
call :log "Python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다."
call :log "Python 3.11 또는 3.12를 설치하세요."
call :log "설치 시 Add python.exe to PATH를 체크하세요."
call :log "설치 후 CMD를 다시 열고 build_windows.bat를 다시 실행하세요."
call :log ""
call :log "Microsoft Store alias 안내:"
call :log "- 현재 python 명령이 Microsoft Store alias로 연결되어 있을 수 있습니다."
call :log "- Windows 설정의 앱 실행 별칭 화면에서 python.exe, python3.exe 별칭을 끄거나, py 명령을 사용하세요."
call :log "- Python이 설치되어 있지만 PATH만 문제라면 다음처럼 직접 경로를 지정할 수 있습니다."
call :log "  set PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
call :log "  build_windows.bat"
exit /b 1

:try_common_python_paths
call :log "Trying common Python install paths..."
call :try_python_file "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PYTHON_CMD exit /b 0
call :try_python_file "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PYTHON_CMD exit /b 0
call :try_python_file "%ProgramFiles%\Python312\python.exe"
if defined PYTHON_CMD exit /b 0
call :try_python_file "%ProgramFiles%\Python311\python.exe"
if defined PYTHON_CMD exit /b 0
call :try_python_file "%ProgramFiles(x86)%\Python312\python.exe"
if defined PYTHON_CMD exit /b 0
call :try_python_file "%ProgramFiles(x86)%\Python311\python.exe"
exit /b 0

:try_python_file
if exist "%~1" (
    call :try_python "%~1"
)
exit /b 0

:try_python
set "CANDIDATE=%*"
set "VERSION_FILE=%TEMP%\privacy_masker_python_version_%RANDOM%.txt"
set "PIP_FILE=%TEMP%\privacy_masker_pip_version_%RANDOM%.txt"
call :log "Trying Python candidate: %CANDIDATE%"

%CANDIDATE% --version > "%VERSION_FILE%" 2>&1
if errorlevel 1 (
    call :append_file "%VERSION_FILE%"
    del "%VERSION_FILE%" >nul 2>nul
    echo %CANDIDATE% | findstr /i /b /c:"python" >nul
    if not errorlevel 1 (
        call :log "현재 python 명령이 Microsoft Store alias로 연결되어 있을 수 있습니다."
        call :log "Windows 설정의 앱 실행 별칭 화면에서 python.exe, python3.exe 별칭을 끄거나, py 명령을 사용하세요."
    )
    call :log "Candidate failed: %CANDIDATE%"
    exit /b 0
)

set "VERSION_OUTPUT="
set /p VERSION_OUTPUT=<"%VERSION_FILE%"
call :append_file "%VERSION_FILE%"
del "%VERSION_FILE%" >nul 2>nul

echo %VERSION_OUTPUT% | findstr /r /c:"Python 3\." >nul
if errorlevel 1 (
    call :log "Candidate did not report a usable Python 3 version: %VERSION_OUTPUT%"
    echo %CANDIDATE% | findstr /i /b /c:"python" >nul
    if not errorlevel 1 (
        call :log "현재 python 명령이 Microsoft Store alias로 연결되어 있을 수 있습니다."
        call :log "Windows 설정의 앱 실행 별칭 화면에서 python.exe, python3.exe 별칭을 끄거나, py 명령을 사용하세요."
    )
    exit /b 0
)

%CANDIDATE% -m pip --version > "%PIP_FILE%" 2>&1
if errorlevel 1 (
    call :append_file "%PIP_FILE%"
    del "%PIP_FILE%" >nul 2>nul
    call :log "Candidate has no working pip: %CANDIDATE%"
    exit /b 0
)

set "PIP_OUTPUT="
set /p PIP_OUTPUT=<"%PIP_FILE%"
call :append_file "%PIP_FILE%"
del "%PIP_FILE%" >nul 2>nul

set "PYTHON_CMD=%CANDIDATE%"
set "PYTHON_VERSION=%VERSION_OUTPUT%"
set "PIP_VERSION=%PIP_OUTPUT%"
call :log "Selected Python: %PYTHON_CMD%"
call :log "Python version: %PYTHON_VERSION%"
call :log "pip version: %PIP_VERSION%"
exit /b 0

:create_or_use_venv
set "FAILED_STAGE=virtual environment setup"
call :log "[2/9] Creating or using .venv..."
if exist "%VENV_PYTHON%" (
    call :log "Using existing virtual environment: %VENV_PYTHON%"
    exit /b 0
)

call :log "Creating virtual environment with: %PYTHON_CMD% -m venv .venv"
%PYTHON_CMD% -m venv .venv >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] Failed to create .venv."
    exit /b 1
)
if not exist "%VENV_PYTHON%" (
    call :log "[ERROR] .venv was created, but %VENV_PYTHON% was not found."
    exit /b 1
)
exit /b 0

:upgrade_pip
set "FAILED_STAGE=pip upgrade"
call :log "[3/9] Upgrading pip..."
"%VENV_PYTHON%" -m pip install --upgrade pip >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] pip upgrade failed."
    exit /b 1
)
for /f "delims=" %%I in ('"%VENV_PYTHON%" -m pip --version 2^>nul') do set "PIP_VERSION=%%I"
call :log "pip version: %PIP_VERSION%"
exit /b 0

:install_requirements
set "FAILED_STAGE=requirements install"
call :log "[4/9] Installing requirements..."
"%VENV_PYTHON%" -m pip install -r requirements.txt >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] requirements.txt installation failed."
    exit /b 1
)
if exist requirements-dev.txt (
    call :log "Installing requirements-dev.txt..."
    "%VENV_PYTHON%" -m pip install -r requirements-dev.txt >> "%BUILD_LOG%" 2>&1
    if errorlevel 1 (
        call :log "[ERROR] requirements-dev.txt installation failed."
        exit /b 1
    )
) else (
    call :log "requirements-dev.txt not found. Continuing."
)
exit /b 0

:ensure_pyinstaller
set "FAILED_STAGE=PyInstaller check"
call :log "[5/9] Checking PyInstaller..."
"%VENV_PYTHON%" -m PyInstaller --version > "%TEMP%\privacy_masker_pyinstaller_version.txt" 2>&1
if errorlevel 1 (
    call :append_file "%TEMP%\privacy_masker_pyinstaller_version.txt"
    call :log "PyInstaller is not available. Installing pyinstaller..."
    "%VENV_PYTHON%" -m pip install pyinstaller >> "%BUILD_LOG%" 2>&1
    if errorlevel 1 (
        call :log "[ERROR] PyInstaller installation failed."
        del "%TEMP%\privacy_masker_pyinstaller_version.txt" >nul 2>nul
        exit /b 1
    )
    "%VENV_PYTHON%" -m PyInstaller --version > "%TEMP%\privacy_masker_pyinstaller_version.txt" 2>&1
    if errorlevel 1 (
        call :append_file "%TEMP%\privacy_masker_pyinstaller_version.txt"
        call :log "[ERROR] PyInstaller is still not available after installation."
        del "%TEMP%\privacy_masker_pyinstaller_version.txt" >nul 2>nul
        exit /b 1
    )
)
set /p PYINSTALLER_VERSION=<"%TEMP%\privacy_masker_pyinstaller_version.txt"
call :append_file "%TEMP%\privacy_masker_pyinstaller_version.txt"
del "%TEMP%\privacy_masker_pyinstaller_version.txt" >nul 2>nul
call :log "PyInstaller version: %PYINSTALLER_VERSION%"
exit /b 0

:run_tests
set "FAILED_STAGE=pytest"
if "%SKIP_TESTS%"=="1" (
    call :log "[6/9] Skipping tests because SKIP_TESTS=1."
    exit /b 0
)
call :log "[6/9] Running tests..."
"%VENV_PYTHON%" -m pytest -q >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] pytest failed. Build stopped."
    call :log "To skip tests for a local diagnostic build only, run:"
    call :log "  set SKIP_TESTS=1"
    call :log "  build_windows.bat"
    exit /b 1
)
call :log "Tests passed."
exit /b 0

:clean_build_dirs
set "FAILED_STAGE=build folder cleanup"
call :log "[7/9] Cleaning build and dist folders..."
if exist build rmdir /s /q build >> "%BUILD_LOG%" 2>&1
if exist dist rmdir /s /q dist >> "%BUILD_LOG%" 2>&1
exit /b 0

:run_pyinstaller
set "FAILED_STAGE=PyInstaller build"
call :log "[8/9] Running PyInstaller..."
"%VENV_PYTHON%" -m PyInstaller privacy_masker.spec --clean -y >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] PyInstaller build failed."
    exit /b 1
)
exit /b 0

:check_exe
set "FAILED_STAGE=exe verification"
call :log "[9/9] Checking executable..."
if exist "dist\PrivacyMasker\PrivacyMasker.exe" (
    call :log "Build success: dist\PrivacyMasker\PrivacyMasker.exe"
    exit /b 0
)
call :log "[ERROR] PyInstaller completed, but executable was not found."
call :log "Expected: dist\PrivacyMasker\PrivacyMasker.exe"
call :log "Check the dist folder structure."
exit /b 1

:build_failed
call :log ""
call :log "[ERROR] Build failed."
call :log "Failed stage: %FAILED_STAGE%"
call :log "Selected Python command: %PYTHON_CMD%"
call :log "Python version: %PYTHON_VERSION%"
call :log "pip version: %PIP_VERSION%"
call :log "PyInstaller version: %PYINSTALLER_VERSION%"
call :log "Log file: %CD%\%BUILD_LOG%"
call :log ""
call :log "Next diagnostic commands:"
call :log "  python --version"
call :log "  py --version"
call :log "  where python"
call :log "  where py"
call :log ""
pause
exit /b 1

:log
if "%~1"=="" (
    echo.
    >> "%BUILD_LOG%" echo.
) else (
    echo %~1
    >> "%BUILD_LOG%" echo %~1
)
exit /b 0

:append_file
if exist %1 (
    type %1
    echo.
    type %1 >> "%BUILD_LOG%"
    >> "%BUILD_LOG%" echo.
)
exit /b 0
