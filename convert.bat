@echo off
pyinstaller --noconsole --onefile --icon=resources/logo_black.png VezylTranslator.py
pause

@echo off
set FILENAME=VezylTranslator

pyinstaller --noconsole --onefile --icon=resources/logo_black.png "%FILENAME%.py"

if exist "dist\%FILENAME%.exe" (
    move /Y "dist\%FILENAME%.exe" ".\%FILENAME%.exe"
)

rmdir /S /Q build
rmdir /S /Q dist
del /Q "%FILENAME%.spec"
