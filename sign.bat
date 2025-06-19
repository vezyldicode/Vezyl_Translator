@echo off
REM === Cấu hình ===
set PYTHON_FILE=VezylTranslator.py
set EXE_NAME=VezylTranslator.exe
set PFX_NAME=vezyltranslator.pfx
set CERT_SUBJECT="CN=VezylTranslator"
set PFX_PASSWORD=yourpassword

REM === Thêm signtool vào PATH (sửa đường dẫn cho đúng bản Windows SDK của bạn) ===
set PATH=%PATH%;C:\Program Files (x86)\Windows Kits\10\bin\10.0.20348.0\x64\signtool.exe

REM === 1. Đóng gói Python thành exe ===
echo [1] Đóng gói %PYTHON_FILE% thành %EXE_NAME%...
pyinstaller --onefile --noconsole %PYTHON_FILE%
if not exist dist\%EXE_NAME% (
    echo Lỗi: Không tìm thấy file dist\%EXE_NAME%
    exit /b 1
)
copy dist\%EXE_NAME% .\%EXE_NAME%

REM === 2. Tạo chứng chỉ tự ký (nếu chưa có) ===
if not exist %PFX_NAME% (
    echo [2] Tạo chứng chỉ tự ký...
    powershell -Command "$cert = New-SelfSignedCertificate -Type CodeSigning -Subject %CERT_SUBJECT% -CertStoreLocation Cert:\CurrentUser\My; $pwd = ConvertTo-SecureString -String '%PFX_PASSWORD%' -Force -AsPlainText; Export-PfxCertificate -Cert $cert -FilePath '%PFX_NAME%' -Password $pwd"
) else (
    echo [2] Đã có chứng chỉ %PFX_NAME%
)

REM === 3. Ký file exe ===
echo [3] Ký file %EXE_NAME%...
set PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.20348.0\x64\signtool.exe";%PATH%
signtool sign /f %PFX_NAME% /p %PFX_PASSWORD% /tr http://timestamp.digicert.com /td sha256 /fd sha256 %EXE_NAME%
if errorlevel 1 (
    echo Lỗi khi ký file!
    exit /b 1
)

REM === 4. Kiểm tra chữ ký ===
echo [4] Kiểm tra chữ ký...
signtool verify /pa /v %EXE_NAME%

echo === Hoàn tất! ===
pause