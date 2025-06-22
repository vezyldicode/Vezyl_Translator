@echo off
set FILENAME=VezylTranslator

REM Create a bootstrap python file that imports the required modules
echo import sys > bootstrap.py
echo import os >> bootstrap.py
echo # Add the current directory to path >> bootstrap.py
echo sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) >> bootstrap.py
echo import Crypto >> bootstrap.py
echo import Crypto.Cipher >> bootstrap.py
echo import Crypto.Cipher.AES >> bootstrap.py
echo import Crypto.Random >> bootstrap.py
echo import pyperclip >> bootstrap.py
echo import pyautogui >> bootstrap.py
echo import customtkinter >> bootstrap.py
echo import PIL >> bootstrap.py
echo import pystray >> bootstrap.py
echo import keyboard >> bootstrap.py
echo import toml >> bootstrap.py
echo import googletrans >> bootstrap.py
echo import winsound >> bootstrap.py
echo # Import the packages >> bootstrap.py
echo import VezylTranslatorNeutron >> bootstrap.py
echo import VezylTranslatorProton >> bootstrap.py
echo import VezylTranslatorElectron >> bootstrap.py
echo try: >> bootstrap.py
echo     from %FILENAME% import main >> bootstrap.py
echo     if __name__ == "__main__": >> bootstrap.py
echo         main() >> bootstrap.py
echo except Exception as e: >> bootstrap.py
echo     import traceback, os >> bootstrap.py
echo     temp_file = os.path.join(os.environ.get('TEMP', '.'), 'VezylTranslator_error_log.txt') >> bootstrap.py
echo     with open(temp_file, "w") as f: >> bootstrap.py
echo         f.write(str(e) + "\n") >> bootstrap.py
echo         f.write(traceback.format_exc()) >> bootstrap.py
echo     import subprocess >> bootstrap.py
echo     import sys >> bootstrap.py
echo     subprocess.Popen(["VezylTranslatorCrashHandler.exe", traceback.format_exc(), "Vezyl Translator", "1.0.0"], creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0) >> bootstrap.py

REM Copy original Python files to dist folder
mkdir dist
copy %FILENAME%.py dist\

REM Using pyarmor gen to encrypt the scripts
pyarmor gen %FILENAME%.py
pyarmor gen bootstrap.py

REM Using PyInstaller to create executable without console
pyinstaller --onefile --noconsole ^
--icon=resources\logo_black_bg.png ^
--hidden-import=Crypto ^
--hidden-import=Crypto.Cipher ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=Crypto.Random ^
--hidden-import=pyperclip ^
--hidden-import=pyautogui ^
--hidden-import=customtkinter ^
--hidden-import=PIL ^
--hidden-import=pystray ^
--hidden-import=keyboard ^
--hidden-import=toml ^
--hidden-import=googletrans ^
--hidden-import=%FILENAME% ^
--hidden-import=VezylTranslatorNeutron ^
--hidden-import=VezylTranslatorProton ^
--hidden-import=VezylTranslatorElectron ^
--hidden-import=winsound ^
--add-data "%FILENAME%.py;." ^
--add-data "dist\%FILENAME%.py;." ^
--add-data "VezylTranslatorNeutron;VezylTranslatorNeutron" ^
--add-data "VezylTranslatorProton;VezylTranslatorProton" ^
--add-data "VezylTranslatorElectron;VezylTranslatorElectron" ^
dist\bootstrap.py

REM Rename the output file
if exist "dist\bootstrap.exe" (
    move /Y "dist\bootstrap.exe" ".\%FILENAME%.exe"
)

REM Cleanup
del bootstrap.py
rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q pyarmor_runtime
del /Q bootstrap.spec