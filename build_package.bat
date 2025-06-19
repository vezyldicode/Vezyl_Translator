@echo off
setlocal

REM 1. Đặt biến version
set "version=1.0.0"

REM 2. Tạo thư mục đích
set "dest=Vezyl_Translator_%version%"
if exist "%dest%" rmdir /s /q "%dest%"
mkdir "%dest%"

REM 3. Copy các file chính
copy /y "VezylTranslator.exe" "%dest%\"
copy /y "README.md" "%dest%\"
copy /y "VezylsTranslatorCrashHandler.exe" "%dest%\"

REM 4. Copy thư mục VezylTranslatorProton, sau đó xóa thư mục con 'local'
xcopy "VezylTranslatorProton" "%dest%\VezylTranslatorProton" /E /I
if exist "%dest%\VezylTranslatorProton\local" rmdir /s /q "%dest%\VezylTranslatorProton\local"

REM 5. Copy thư mục resources, sau đó xóa thư mục con 'neveruse'
xcopy "resources" "%dest%\resources" /E /I
if exist "%dest%\resources\neveruse" rmdir /s /q "%dest%\resources\neveruse"

REM 6. Copy thư mục config
xcopy "config" "%dest%\config" /E /I

echo Đã hoàn thành đóng gói phiên bản