@echo off
set FILENAME=VezylTranslator

echo ===============================================
echo � ONEDIR BUILD - Faster Startup  
echo ===============================================

REM Check bootstrap template exists
if not exist "bootstrap_onedir_build.py" (
    echo ❌ ERROR: bootstrap_onedir_build.py not found!
    echo Please make sure the template file exists.
    pause
    exit /b 1
)

REM Create distribution folder
mkdir dist_onedir
copy %FILENAME%.py dist_onedir\

REM Encrypt with pyarmor (onedir protection)
echo 🔒 Encrypting files with PyArmor...
pyarmor gen --output dist_onedir bootstrap_onedir_build.py
if not exist "dist_onedir\bootstrap_onedir_build.py" (
    echo ⚠️  PyArmor encryption failed, using original bootstrap
    copy bootstrap_onedir_build.py dist_onedir\
)

pyarmor gen --output dist_onedir %FILENAME%.py
if not exist "dist_onedir\%FILENAME%.py" (
    echo ⚠️  PyArmor encryption failed for main file
)

REM Build with PyInstaller - ONEDIR mode for faster startup
echo 📦 Building onedir executable...

REM Check if encrypted file exists
if exist "dist_onedir\bootstrap_onedir_build.py" (
    echo ✅ Using encrypted bootstrap_onedir_build.py
    set "BOOTSTRAP_FILE=dist_onedir\bootstrap_onedir_build.py"
) else (
    echo ⚠️  Encrypted file not found, using original
    set "BOOTSTRAP_FILE=bootstrap_onedir_build.py"
)

echo Using bootstrap file: %BOOTSTRAP_FILE%

pyinstaller --onedir ^
--noconsole ^
--icon=resources\logo_black.ico ^
--optimize=2 ^
--clean ^
--noconfirm ^
--hidden-import=tkinter ^
--hidden-import=tkinter.ttk ^
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
--hidden-import=Crypto ^
--hidden-import=Crypto.Cipher ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=Crypto.Random ^
--exclude-module=transformers ^
--exclude-module=torch ^
--exclude-module=tensorflow ^
--exclude-module=matplotlib ^
--exclude-module=scipy ^
--exclude-module=pandas ^
--exclude-module=sklearn ^
--exclude-module=numpy ^
--exclude-module=cv2 ^
--exclude-module=IPython ^
--exclude-module=jupyter ^
--add-data "config;config" ^
--add-data "resources;resources" ^
--add-data "VezylTranslatorCrashHandler.exe;." ^
--add-data "%FILENAME%.py;." ^
--add-data "dist_onedir;." ^
--add-data "VezylTranslatorNeutron;VezylTranslatorNeutron" ^
--add-data "VezylTranslatorProton;VezylTranslatorProton" ^
--add-data "VezylTranslatorElectron;VezylTranslatorElectron" ^
--name %FILENAME% ^
%BOOTSTRAP_FILE%

REM Check build result
if exist "dist\%FILENAME%" (
    echo.
    echo ===============================================
    echo ✅ ONEDIR BUILD COMPLETED!
    echo ===============================================
    echo.
    echo 🎯 Features:
    echo - ONEDIR build for faster startup
    echo - Minimal imports in bootstrap
    echo - Smaller file size per component
    echo - Quick loading screen
    echo - PyArmor protection maintained
    echo.
    echo 📁 Output: dist\%FILENAME%\
    echo.
    
    echo 🧹 Cleaning up and organizing files...
    
    REM Move built files to root directory
    echo - Moving %FILENAME%.exe to root...
    move "dist\%FILENAME%\%FILENAME%.exe" . >nul 2>&1
    
    echo - Moving _internal folder to root...
    if exist "_internal" rmdir /S /Q "_internal"
    robocopy "dist\%FILENAME%\_internal" "_internal" /E /MOVE /NFL /NDL /NJH /NJS
    
    REM Clean up build folders
    echo - Removing build artifacts...
    rmdir /S /Q "dist" 2>nul
    rmdir /S /Q "dist_onedir" 2>nul
    rmdir /S /Q "build" 2>nul
    rmdir /S /Q "__pycache__" 2>nul
    del /Q "%FILENAME%.spec" 2>nul
    
    echo.
    echo ===============================================
    echo ✅ BUILD AND CLEANUP COMPLETED!
    echo ===============================================
    echo.
    echo 🎯 Final structure:
    echo - %FILENAME%.exe (in root)
    echo - _internal\ (folder in root)
    echo.
    echo 🚀 Ready to run: %FILENAME%.exe
    echo.
) else (
    echo.
    echo ❌ ERROR: OneDir build failed!
    pause
    exit /b 1
)
