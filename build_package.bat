@echo off
setlocal

REM 1. Đặt biến version
set "version=1.5.1"

REM 2. Tạo thư mục đích
set "dest=Vezyl_Translator_%version%"
if exist "%dest%" rmdir /s /q "%dest%"
mkdir "%dest%"

REM 3. Copy các file chính
move /y "VezylTranslator.exe" "%dest%\"
copy /y "README.md" "%dest%\"
copy /y "VezylTranslatorCrashHandler.exe" "%dest%\"

REM 4. move thư mục _internal
move "_internal" "%dest%\_internal"

REM 7. Copy thư mục resources, sau đó xóa thư mục con 'neveruse'
xcopy "resources" "%dest%\resources" /E /I
if exist "%dest%\resources\neveruse" rmdir /s /q "%dest%\resources\neveruse"

REM 8. Copy thư mục config
xcopy "config" "%dest%\config" /E /I

echo Đã hoàn thành đóng gói phiên bản