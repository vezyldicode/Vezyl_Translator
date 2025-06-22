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
copy /y "VezylTranslatorCrashHandler.exe" "%dest%\"

REM 4. Copy thư mục VezylTranslatorProton, sau đó xóa thư mục con 'local'
xcopy "VezylTranslatorProton" "%dest%\VezylTranslatorProton" /E /I
if exist "%dest%\VezylTranslatorProton\local" rmdir /s /q "%dest%\VezylTranslatorProton\local"

REM 5. Copy thư mục VezylTranslatorNeutron, sau đó xóa thư mục con 'local'
xcopy "VezylTranslatorNeutron" "%dest%\VezylTranslatorNeutron" /E /I
if exist "%dest%\VezylTranslatorNeutron\local" rmdir /s /q "%dest%\VezylTranslatorNeutron\local"

REM 6. Copy thư mục VezylTranslatorElectron, sau đó xóa thư mục con 'local'
xcopy "VezylTranslatorElectron" "%dest%\VezylTranslatorElectron" /E /I
if exist "%dest%\VezylTranslatorElectron\local" rmdir /s /q "%dest%\VezylTranslatorElectron\local"

REM 7. Copy thư mục resources, sau đó xóa thư mục con 'neveruse'
xcopy "resources" "%dest%\resources" /E /I
if exist "%dest%\resources\neveruse" rmdir /s /q "%dest%\resources\neveruse"

REM 8. Copy thư mục config
xcopy "config" "%dest%\config" /E /I

echo Đã hoàn thành đóng gói phiên bản