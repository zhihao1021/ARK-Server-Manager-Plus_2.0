@ECHO OFF
@REM @ping 127.0.0.1 -n 1 -w 1000 > nul
git stash
git pull
.\.venv\Scripts\activate.bat && python main.py