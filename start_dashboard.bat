@echo off
rem Startet das WM-Dashboard und oeffnet den Browser.
cd /d "%~dp0"
start "" http://127.0.0.1:5050
python app.py
