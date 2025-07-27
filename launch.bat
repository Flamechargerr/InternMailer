@echo off
echo 🚀 Starting InternMailer...
echo.
echo Open your browser to: http://localhost:8505
echo Press Ctrl+C to stop the application
echo.

cd /d "C:\Users\anama\OneDrive\Desktop\internmailing\InternMailer"
streamlit run app.py --server.port=8505

pause
