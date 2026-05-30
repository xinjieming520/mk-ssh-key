@echo off

REM --- 配置区（根据需要修改以下变量）---

REM 密钥备注信息（建议邮箱）
set "COMMENT=xinjieming85@gmail.com"

REM 支持: ed25519(推荐) / rsa / ecdsa
set "ALGORITHM=ed25519"

REM 密钥目录（可自定义）
set "SSH_KEY_DIR=%USERPROFILE%\.ssh\new-key"

REM 密钥文件名
set "KEY_NAME=id_ed25519"

REM 1=使用密码, 0=无密码
set "USE_PASSPHRASE=0"

REM --- 配置区结束 ---
