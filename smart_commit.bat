@echo off
echo ================================================
echo    Smart Git Commit for VezylTranslator
echo ================================================
echo.

echo Committing changes in smaller chunks to avoid GitHub size limits...
echo.

REM Reset all staged changes first
git reset HEAD .

REM Commit 1: Configuration files
echo [1/5] Committing configuration files...
git add .gitignore
git add config/*.json
if exist config\*.toml git add config\*.toml
git commit -m "Update configuration files and gitignore"

REM Commit 2: Main application files
echo [2/5] Committing main application files...
git add VezylTranslator.py
git add requirements.txt
git commit -m "Update main application and dependencies"

REM Commit 3: Proton modules (excluding large files)
echo [3/5] Committing Proton modules...
git add VezylTranslatorProton\*.py
git add VezylTranslatorProton\local\*.py
git commit -m "Update VezylTranslatorProton modules"

REM Commit 4: Electron modules
echo [4/5] Committing Electron modules...
git add VezylTranslatorElectron\*.py
git add VezylTranslatorElectron\local\*.py
git commit -m "Update VezylTranslatorElectron modules"

REM Commit 5: Other files (excluding large ones)
echo [5/5] Committing remaining files...
git add *.py
git add *.bat
git add *.md
git add *.txt
git add resources\*.png
git add resources\*.ico
git add resources\*.json
git add resources\locales\*
REM Explicitly exclude marian_models directory
git reset HEAD resources\marian_models\ 2>nul
git commit -m "Update remaining application files"

echo.
echo ================================================
echo All commits completed!
echo Repository is now ready for push.
echo.
echo Run: git push origin main
echo ================================================
pause
