@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PYTHON=python"

REM Ensure venv exists
if not exist "%SCRIPT_DIR%.venv" (
  echo Creating virtual environment...
  %PYTHON% -m venv "%SCRIPT_DIR%.venv"
)

REM Paths
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "HASH_FILE=%SCRIPT_DIR%.requirements.hash"

REM Calculate MD5 of requirements.txt
for /f "usebackq tokens=1 delims= " %%A in (`certutil -hashfile "%REQUIREMENTS%" MD5 ^| find /i /v "hash"`) do set "REQ_HASH=%%A"

REM Activate venv
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"

REM Check if requirements changed
set "OLD_HASH="
if exist "%HASH_FILE%" (
  for /f "usebackq delims=" %%B in ("%HASH_FILE%") do set "OLD_HASH=%%B"
)

echo Current requirements hash: %REQ_HASH%
echo Previous requirements hash: %OLD_HASH%

set INSTALL_REQ=0
if not defined OLD_HASH (
  set INSTALL_REQ=1
) else (
  if /i "%OLD_HASH%" NEQ "%REQ_HASH%" set INSTALL_REQ=1
)

REM Install if needed
if %INSTALL_REQ%==1 (
  echo Installing dependencies...
  python -m pip install --upgrade pip
  pip install -r "%REQUIREMENTS%"
  > "%HASH_FILE%" (
    <nul set /p="%REQ_HASH%"
  )
) else (
  echo Dependencies unchanged, skipping installation.
)

echo Starting application...
start "" "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" "%SCRIPT_DIR%main.py"

endlocal
exit /b
