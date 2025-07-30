@echo off
set FILENAME=VezylTranslator

REM Create a bootstrap with immediate loading screen and full imports
echo import sys > bootstrap.py
echo import os >> bootstrap.py
echo import time >> bootstrap.py
echo import threading >> bootstrap.py
echo import tkinter as tk >> bootstrap.py
echo from tkinter import ttk >> bootstrap.py
echo # Set up environment >> bootstrap.py
echo sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) >> bootstrap.py
echo. >> bootstrap.py
echo class LoadingScreen: >> bootstrap.py
echo     def __init__(self): >> bootstrap.py
echo         self.root = tk.Tk() >> bootstrap.py
echo         self.root.title("VezylTranslator") >> bootstrap.py
echo         self.root.geometry("400x200") >> bootstrap.py
echo         self.root.resizable(False, False) >> bootstrap.py
echo         self.root.configure(bg='#2b2b2b') >> bootstrap.py
echo         # Center window >> bootstrap.py
echo         self.root.eval('tk::PlaceWindow . center') >> bootstrap.py
echo         # Logo and title >> bootstrap.py
echo         title = tk.Label(self.root, text="Vezyl Translator", font=("Arial", 16, "bold"), fg="white", bg="#2b2b2b") >> bootstrap.py
echo         title.pack(pady=20) >> bootstrap.py
echo         # Progress bar >> bootstrap.py
echo         self.progress = ttk.Progressbar(self.root, mode='indeterminate', length=300) >> bootstrap.py
echo         self.progress.pack(pady=10) >> bootstrap.py
echo         self.progress.start(10) >> bootstrap.py
echo         # Status label >> bootstrap.py
echo         self.status = tk.Label(self.root, text="Initializing...", font=("Arial", 10), fg="#cccccc", bg="#2b2b2b") >> bootstrap.py
echo         self.status.pack(pady=5) >> bootstrap.py
echo         # Debug info >> bootstrap.py
echo         self.debug = tk.Label(self.root, text="", font=("Arial", 8), fg="#888888", bg="#2b2b2b") >> bootstrap.py
echo         self.debug.pack(pady=5) >> bootstrap.py
echo         self.root.update() >> bootstrap.py
echo. >> bootstrap.py
echo     def update_status(self, message, debug_info=""): >> bootstrap.py
echo         self.status.config(text=message) >> bootstrap.py
echo         if debug_info: >> bootstrap.py
echo             self.debug.config(text=debug_info) >> bootstrap.py
echo         self.root.update() >> bootstrap.py
echo         print(f"[LOADING] {message} {debug_info}") >> bootstrap.py
echo. >> bootstrap.py
echo     def close(self): >> bootstrap.py
echo         self.progress.stop() >> bootstrap.py
echo         self.root.destroy() >> bootstrap.py
echo. >> bootstrap.py
echo # Show loading screen immediately >> bootstrap.py
echo loader = LoadingScreen() >> bootstrap.py
echo start_time = time.time() >> bootstrap.py
echo. >> bootstrap.py
echo try: >> bootstrap.py
echo     # Import all required modules with progress updates >> bootstrap.py
echo     loader.update_status("Loading system modules...", "sys, os, threading") >> bootstrap.py
echo     import Crypto >> bootstrap.py
echo     import Crypto.Cipher >> bootstrap.py
echo     import Crypto.Cipher.AES >> bootstrap.py
echo     import Crypto.Random >> bootstrap.py
echo     loader.update_status("Crypto modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     import winsound >> bootstrap.py
echo     import customtkinter >> bootstrap.py
echo     loader.update_status("GUI modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     import PIL >> bootstrap.py
echo     import pyperclip >> bootstrap.py
echo     import pyautogui >> bootstrap.py
echo     loader.update_status("System integration loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     import pystray >> bootstrap.py
echo     import keyboard >> bootstrap.py
echo     loader.update_status("Input modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     import toml >> bootstrap.py
echo     import json >> bootstrap.py
echo     import requests >> bootstrap.py
echo     loader.update_status("Network modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     import googletrans >> bootstrap.py
echo     import langdetect >> bootstrap.py
echo     loader.update_status("Translation modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     # Import VezylTranslator modules >> bootstrap.py
echo     loader.update_status("Loading VezylTranslator...", "Core modules") >> bootstrap.py
echo     import VezylTranslatorNeutron >> bootstrap.py
echo     import VezylTranslatorProton >> bootstrap.py
echo     import VezylTranslatorElectron >> bootstrap.py
echo     loader.update_status("VezylTranslator modules loaded", f"{time.time() - start_time:.1f}s") >> bootstrap.py
echo. >> bootstrap.py
echo     # Import main application >> bootstrap.py
echo     loader.update_status("Starting application...", "Loading main") >> bootstrap.py
echo     from %FILENAME% import main >> bootstrap.py
echo     loading_time = time.time() - start_time >> bootstrap.py
echo     loader.update_status("Ready!", f"Total: {loading_time:.1f}s") >> bootstrap.py
echo     time.sleep(0.5)  # Brief pause to show final status >> bootstrap.py
echo     loader.close() >> bootstrap.py
echo. >> bootstrap.py
echo     if __name__ == "__main__": >> bootstrap.py
echo         main() >> bootstrap.py
echo. >> bootstrap.py
echo except Exception as e: >> bootstrap.py
echo     loader.update_status("Error occurred!", str(e)) >> bootstrap.py
echo     time.sleep(2) >> bootstrap.py
echo     loader.close() >> bootstrap.py
echo     # Error handling >> bootstrap.py
echo     try: >> bootstrap.py
echo         with open("startup_error.log", "w") as f: >> bootstrap.py
echo             f.write("Bootstrap error: " + str(e)) >> bootstrap.py
echo         import subprocess >> bootstrap.py
echo         subprocess.Popen(["VezylTranslatorCrashHandler.exe", str(e), "Vezyl Translator", "1.0.0"]) >> bootstrap.py
echo     except: >> bootstrap.py
echo         pass >> bootstrap.py

REM Copy original Python files to dist folder
mkdir dist
copy %FILENAME%.py dist\

REM Using pyarmor gen to encrypt the scripts
pyarmor gen %FILENAME%.py
pyarmor gen bootstrap.py

REM Using PyInstaller with all required imports for loading screen
pyinstaller --onefile --noconsole ^
--icon=resources\logo_black.ico ^
--optimize=2 ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
--hidden-import=Crypto ^
--hidden-import=Crypto.Cipher ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=Crypto.Random ^
--hidden-import=winsound ^
--hidden-import=customtkinter ^
--hidden-import=PIL ^
--hidden-import=pyperclip ^
--hidden-import=pyautogui ^
--hidden-import=pystray ^
--hidden-import=keyboard ^
--hidden-import=toml ^
--hidden-import=json ^
--hidden-import=requests ^
--hidden-import=googletrans ^
--hidden-import=langdetect ^
--hidden-import=%FILENAME% ^
--hidden-import=VezylTranslatorNeutron ^
--hidden-import=VezylTranslatorProton ^
--hidden-import=VezylTranslatorElectron ^
--exclude-module=transformers ^
--exclude-module=torch ^
--exclude-module=tensorflow ^
--exclude-module=matplotlib ^
--exclude-module=scipy ^
--exclude-module=pandas ^
--exclude-module=sklearn ^
--add-data "config;config" ^
--add-data "resources;resources" ^
--add-data "VezylTranslatorCrashHandler.exe;." ^
--add-data "%FILENAME%.py;." ^
--add-data "dist\%FILENAME%.py;." ^
--add-data "VezylTranslatorNeutron;VezylTranslatorNeutron" ^
--add-data "VezylTranslatorProton;VezylTranslatorProton" ^
--add-data "VezylTranslatorElectron;VezylTranslatorElectron" ^
dist\bootstrap.py

REM Rename the output file
if exist "dist\bootstrap.exe" (
    move /Y "dist\bootstrap.exe" ".\%FILENAME%.exe"
    echo.
    echo ===============================================
    echo ✅ SUCCESS: %FILENAME%.exe created with loading screen!
    echo ===============================================
    echo.
    echo Features:
    echo - Immediate loading screen on startup
    echo - Progress indicator with timing
    echo - Debug information display
    echo - All required modules included
    echo.
    echo Testing the executable...
    start /b %FILENAME%.exe
    echo.
    echo Watch the loading screen for timing information!
) else (
    echo.
    echo ❌ ERROR: Build failed!
    pause
    exit /b 1
)

REM Cleanup
del bootstrap.py
rmdir /S /Q dist
rmdir /S /Q build
rmdir /S /Q pyarmor_runtime
del /Q bootstrap.spec