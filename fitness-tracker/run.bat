@echo off
echo.
echo  Fitness Tracker
echo  ---------------
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP: =%
echo  Local access:   http://localhost:8000
echo  Phone access:   http://%IP%:8000
echo.
echo  Starting server...
echo.
cd /d "%~dp0"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
