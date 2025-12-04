@echo off
cd /d "D:\Research\Narm_Afzar\4_Wave\SW_Transform\SRC"
call "D:\Research\Narm_Afzar\4_Wave\SW_Transform\SRC\.venv\Scripts\activate.bat"
python "D:\Research\Narm_Afzar\4_Wave\SW_Transform\run.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    pause >nul
)
