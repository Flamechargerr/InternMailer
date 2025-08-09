@echo off
echo ================================================
echo 📦 INSTALLING ULTRA CAMPAIGN DEPENDENCIES
echo ================================================
echo.

echo 🔧 Installing required Python packages...
echo.

pip install --upgrade pip
pip install pandas
pip install requests
pip install aiohttp
pip install asyncio
pip install python-dateutil
pip install unicodedata2
pip install pathlib

echo.
echo ✅ Dependencies installed successfully!
echo.
echo 🚀 You can now run the Ultra Improved Campaign System v2.0
echo    Use: run_ultra_campaign_v2.bat
echo.
pause
