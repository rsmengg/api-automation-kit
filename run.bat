@echo off
:: Windows 一键运行（你的主力机是 Windows，这个必须能用）
cd /d "%~dp0"
start /B python mock_api.py
timeout /t 2 /nobreak >nul
python -m pytest --base-url http://127.0.0.1:8899 --alluredir=reports\allure-results %*
if exist reports\allure-results if "%~1"=="" (
  allure generate reports\allure-results -o reports\allure-report --clean
)
taskkill /FI "IMAGENAME eq python.exe" /F >nul 2>&1
