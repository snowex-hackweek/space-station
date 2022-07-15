@ECHO OFF
call C:\ProgramData\Anaconda3\Scripts\activate.bat
set root=dash-env
echo Activating Python Virtual Environment...
call activate %root%
echo dash-env Activated!
call cd %~dp0
python app.py -d
pause