@echo off
setlocal EnableDelayedExpansion
set FILENAME=VezylTranslator
set BUILD_START_TIME=%TIME%

echo.
echo ===============================================
echo VEZYL TRANSLATOR - ONEDIR BUILD SYSTEM
echo ===============================================
echo Build started at: %BUILD_START_TIME%
echo Project: %FILENAME%
echo Mode: OneDir (Faster Startup)
echo ===============================================
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...
if not exist "bootstrap_onedir_build.py" (
    echo ERROR: bootstrap_onedir_build.py not found!
    echo Please make sure the bootstrap template exists in the project directory.
    echo Current directory: %CD%
    pause
    exit /b 1
)

if not exist "%FILENAME%.py" (
    echo ERROR: %FILENAME%.py not found!
    echo Please make sure the main Python file exists.
    pause
    exit /b 1
)

echo Bootstrap template found
echo Main Python file found

REM Create distribution folder
echo.
echo [2/6] Preparing build directories...
if exist "dist_onedir" (
    echo Cleaning existing dist_onedir...
    rmdir /S /Q "dist_onedir" >nul 2>&1
)
mkdir "dist_onedir" >nul 2>&1
if not exist "dist_onedir" (
    echo ERROR: Failed to create dist_onedir directory!
    pause
    exit /b 1
)

echo Copying main files...
copy "%FILENAME%.py" "dist_onedir\" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo ERROR: Failed to copy %FILENAME%.py!
    pause
    exit /b 1
)
echo Build directories prepared

echo.
echo [3/6] Code protection (PyArmor)...
echo Attempting to encrypt bootstrap file...

REM Check if PyArmor is available
pyarmor --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo PyArmor not found in PATH - skipping encryption
    echo Using original files without protection
    copy "bootstrap_onedir_build.py" "dist_onedir\" >nul 2>&1
    goto :skip_pyarmor
)

REM Encrypt bootstrap file
pyarmor gen --output "dist_onedir" "bootstrap_onedir_build.py" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo Bootstrap encryption failed - using original
    copy "bootstrap_onedir_build.py" "dist_onedir\" >nul 2>&1
) else (
    echo Bootstrap file encrypted successfully
)

REM Encrypt main file
echo Attempting to encrypt main file...
pyarmor gen --output "dist_onedir" "%FILENAME%.py" >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo Main file encryption failed - build will continue
) else (
    echo Main file encrypted successfully
)

:skip_pyarmor
if not exist "dist_onedir\bootstrap_onedir_build.py" (
    echo ERROR: Bootstrap file missing after encryption step!
    pause
    exit /b 1
)

echo.
echo [4/6] PyInstaller compilation...

REM Determine bootstrap file to use
if exist "dist_onedir\bootstrap_onedir_build.py" (
    set "BOOTSTRAP_FILE=dist_onedir\bootstrap_onedir_build.py"
    echo Using encrypted bootstrap file
) else (
    set "BOOTSTRAP_FILE=bootstrap_onedir_build.py"
    echo Using original bootstrap file
)

echo Bootstrap: !BOOTSTRAP_FILE!
echo Starting PyInstaller compilation...
echo This may take several minutes, please wait...

REM Execute PyInstaller with comprehensive settings
pyinstaller --onedir ^
--noconsole ^
--clean ^
--icon=resources\logo_black.ico ^
--optimize=2 ^
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
--hidden-import=configparser ^
--hidden-import=requests ^
--hidden-import=googletrans ^
--hidden-import=langdetect ^
--hidden-import=os ^
--hidden-import=sys ^
--hidden-import=time ^
--hidden-import=subprocess ^
--hidden-import=Crypto ^
--hidden-import=Crypto.Cipher ^
--hidden-import=Crypto.Cipher.AES ^
--hidden-import=Crypto.Random ^
--hidden-import=base64 ^
--hidden-import=pathlib ^
--hidden-import=dataclasses ^
--hidden-import=typing ^
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
!BOOTSTRAP_FILE! >build_log.txt 2>&1

REM Check PyInstaller exit code
if !ERRORLEVEL! neq 0 (
    echo ERROR: PyInstaller compilation failed!
    echo Build log saved to: build_log.txt
    echo Last 10 lines of build log:
    echo ----------------------------------------
    powershell "Get-Content build_log.txt | Select-Object -Last 10"
    echo ----------------------------------------
    echo Common solutions:
    echo    - Check if all dependencies are installed
    echo    - Verify Python environment is correct
    echo    - Ensure no files are locked by other processes
    pause
    exit /b 1
)

echo PyInstaller compilation completed successfully

echo.
echo [5/6] Verifying build output...

REM Check if executable was created
if not exist "dist\%FILENAME%\%FILENAME%.exe" (
    echo ERROR: Executable not found after compilation!
    echo Expected location: dist\%FILENAME%\%FILENAME%.exe
    echo Checking what was actually created...
    if exist "dist" (
        echo Contents of dist directory:
        dir /B "dist" 2>nul
        if exist "dist\%FILENAME%" (
            echo Contents of dist\%FILENAME% directory:
            dir /B "dist\%FILENAME%" 2>nul
        )
    ) else (
        echo No dist directory found!
    )
    echo Build log available in: build_log.txt
    pause
    exit /b 1
)

echo Executable created successfully
echo Checking file size...
for %%F in ("dist\%FILENAME%\%FILENAME%.exe") do (
    set FILE_SIZE=%%~zF
    set /a "SIZE_MB=!FILE_SIZE!/1048576"
    echo Executable size: !SIZE_MB! MB
)

echo.
echo [6/6] Organizing and cleaning up...

REM Create backup location info
echo Creating build info...
echo Build Date: %DATE% %TIME% > build_info.txt
echo Build Type: OneDir >> build_info.txt
echo File Size: !SIZE_MB! MB >> build_info.txt

REM Move files to root directory
echo Moving executable to root...
if exist "%FILENAME%.exe" (
    echo Removing existing executable...
    del "%FILENAME%.exe" >nul 2>&1
)
move "dist\%FILENAME%\%FILENAME%.exe" . >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo Failed to move executable to root
    echo Executable remains in: dist\%FILENAME%\
    goto :skip_move
)

echo Moving _internal folder...
if exist "_internal" (
    echo Removing existing _internal...
    rmdir /S /Q "_internal" >nul 2>&1
)
robocopy "dist\%FILENAME%\_internal" "_internal" /E /MOVE /NFL /NDL /NJH /NJS >nul 2>&1
if !ERRORLEVEL! gtr 3 (
    echo Issues moving _internal folder (Error: !ERRORLEVEL!)
    echo _internal remains in: dist\%FILENAME%\_internal
)

:skip_move
echo Cleaning build artifacts...
rmdir /S /Q "dist" >nul 2>&1
rmdir /S /Q "dist_onedir" >nul 2>&1  
rmdir /S /Q "build" >nul 2>&1
rmdir /S /Q "__pycache__" >nul 2>&1
del /Q "%FILENAME%.spec" >nul 2>&1
del /Q "build_log.txt" >nul 2>&1

REM Final verification and summary
echo.
set BUILD_END_TIME=%TIME%
echo ===============================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ===============================================
echo.
echo BUILD SUMMARY:
echo Started:  %BUILD_START_TIME%
echo Finished: %BUILD_END_TIME%
echo Size:     !SIZE_MB! MB
echo.
pause
if exist "%FILENAME%.exe" (
    echo FINAL STRUCTURE (Root Directory):
    echo %FILENAME%.exe
    echo _internal\ (dependencies)
    echo config\ (configuration files)  
    echo resources\ (assets)
    echo build_info.txt
    echo.
    echo Ready to run: %FILENAME%.exe
    echo You can now move these files to your desired folder
) else (
    echo BUILD OUTPUT LOCATION:
    echo dist\%FILENAME%\
    echo %FILENAME%.exe
    echo _internal\ (dependencies)
    echo.
    echo Files are ready in the dist folder
)

echo.
echo Build process completed successfully!
echo ===============================================
echo.
