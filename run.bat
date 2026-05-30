@echo off
REM ============================================
REM SSH 密钥生成工具 - 快捷启动脚本
REM ============================================
chcp 65001 >nul
cd /d "%~dp0"

REM --- 默认配置 ---
set "COMMENT=my-email@example.com"
set "ALGORITHM=ed25519"
set "SSH_KEY_DIR=%USERPROFILE%\.ssh\new-key"
set "KEY_NAME="
set "USE_PASSPHRASE=0"

REM --- 加载本地配置 ---
if exist "config.local.bat" call "config.local.bat"

REM --- 解析命令行参数（优先级最高）---
:parse_args
if "%1"=="" goto :end_parse
if /i "%1"=="--no-passphrase" set "USE_PASSPHRASE=0" & shift & goto :parse_args
if /i "%1"=="--dir" set "SSH_KEY_DIR=%~2" & shift & shift & goto :parse_args
if /i "%1"=="--name" set "KEY_NAME=%~2" & shift & shift & goto :parse_args
if /i "%1"=="--comment" set "COMMENT=%~2" & shift & shift & goto :parse_args
if /i "%1"=="--algo" set "ALGORITHM=%~2" & shift & shift & goto :parse_args
if /i "%1"=="--help" goto :show_help
if /i "%1"=="-h" goto :show_help
echo [ERROR] 未知参数: %1
goto :show_help
:end_parse

REM 如果未指定文件名，根据算法设置默认文件名
if "%KEY_NAME%"=="" set "KEY_NAME=id_%ALGORITHM%"

REM 最终确定完整路径
set "FULL_KEY_PATH=%SSH_KEY_DIR%\%KEY_NAME%"

REM --- 显示配置 ---
cls
echo =========================================
echo   SSH 密钥生成工具
echo =========================================
echo.
echo 密钥算法:   %ALGORITHM%
echo 密钥注释:   %COMMENT%
echo 输出目录:   %SSH_KEY_DIR%
echo 文件名:     %KEY_NAME%
echo 完整路径:   %FULL_KEY_PATH%
echo 使用密码:   %USE_PASSPHRASE% (0=无密码 1=有密码)
echo.
echo =========================================
echo.

REM --- 确认生成 ---
set /p "confirm=是否继续生成密钥？(Y/N): "
if /i not "%confirm%"=="y" (
    echo 已取消操作。
    pause
    exit /b 0
)

REM --- 调用 PowerShell 脚本 ---
echo.
echo [INFO] 正在生成 SSH 密钥...
echo.

set "PS_ARGS=-Comment '%COMMENT%' -Algorithm %ALGORITHM% -OutputPath '%FULL_KEY_PATH%'"

if "%USE_PASSPHRASE%"=="0" (
    set "PS_ARGS=%PS_ARGS% -NoPassphrase"
)

powershell -ExecutionPolicy Bypass -File ".\generate-ssh-key.ps1" %PS_ARGS%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 密钥生成失败，错误代码: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================
echo   密钥生成完成！
echo =========================================
echo.
echo 公钥已保存到: %FULL_KEY_PATH%.pub
echo.
echo 下一步:
echo 1. 复制公钥内容
echo 2. 访问 https://github.com/settings/keys
echo 3. 添加新的 SSH 密钥
echo.
echo 测试连接:
echo   ssh -T git@host
echo.
echo 如果使用自定义目录，请更新 ~/.ssh/config 中的 IdentityFile 路径
echo.
pause
exit /b 0

:show_help
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   --no-passphrase       生成无密码短语的密钥
echo   --dir ^<路径^>         指定密钥存储目录
echo   --name ^<文件名^>      指定密钥文件名
echo   --comment ^<注释^>    指定密钥注释
echo   --algo ^<算法^>        指定密钥算法 (ed25519/rsa/ecdsa)
echo   -h, --help            显示此帮助信息
echo.
echo 示例:
echo   %~nx0                                         使用默认配置
echo   %~nx0 --no-passphrase                        生成无密码密钥
echo   %~nx0 --dir "C:\mykeys" --name "github_key"  自定义目录和文件名
echo   %~nx0 --dir "%%USERPROFILE%%\.ssh\work"      使用工作目录
echo.
pause
exit /b 0