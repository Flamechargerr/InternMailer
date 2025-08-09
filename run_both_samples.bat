@echo off
setlocal ENABLEDELAYEDEXPANSION

if "%TEST_RECIPIENT_EMAIL%"=="" (
  set "TEST_RECIPIENT_EMAIL=tripathy.anamay23@gmail.com"
)

echo Using recipient: %TEST_RECIPIENT_EMAIL%
python -u tools\run_both_samples.py
if errorlevel 1 (
  echo run_both_samples.py exited with code %errorlevel%
)
