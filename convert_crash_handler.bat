@echo off
set FILENAME=VezylTranslatorCrashHandler

pyinstaller --noconsole --onefile "%FILENAME%.py"

if exist "dist\%FILENAME%.exe" (
    move /Y "dist\%FILENAME%.exe" ".\%FILENAME%.exe"
)

rmdir /S /Q build
rmdir /S /Q dist
del /Q "%FILENAME%.spec"
