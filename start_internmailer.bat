@echo off
echo.
echo ========================================
echo   InternMailer - AI Email Outreach
echo ========================================
echo.
echo Starting InternMailer application...
echo.
cd /d "C:\Users\anama\OneDrive\Desktop\internmailing\InternMailer"
echo Current directory: %CD%
echo.
echo Checking required files...
if exist "data\proffesor.csv" (
    echo ✓ Professor database found
) else (
    echo ❌ Professor database not found
    pause
    exit /b 1
)

if exist "app.py" (
    echo ✓ Main application found
) else (
    echo ❌ Main application not found
    pause
    exit /b 1
)

echo.
echo ✓ All required files found
echo.
echo Starting Streamlit app...
echo This will open in your default browser automatically.
echo The application will be available at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application.
echo.
streamlit run app.py --server.headless false --server.runOnSave true
pause
