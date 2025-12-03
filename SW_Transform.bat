@echo off
call "D:\Research\Softwars\Geopsy\Land_streamer\.venv\Scripts\activate.bat"
python "D:\Research\Narm_Afzar\4_Wave\SW_Transform\run.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    pause >nul
)
