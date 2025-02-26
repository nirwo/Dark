@echo off
echo === Dark Web Intelligence Scanner Virtual Environment Setup ===
echo Creating Python virtual environment...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Setup complete!
echo To activate the virtual environment in the future, run:
echo     venv\Scripts\activate
echo To deactivate the virtual environment, simply run:
echo     deactivate
echo To run the application, use:
echo     python app.py
echo.
