@echo off

REM --- 本地个人配置（在此处修改将覆盖默认值）---

REM 密钥备注信息（建议填写你的邮箱）
set "COMMENT=xinjieming85@gmail.com"

REM 加密算法: ed25519(推荐) / rsa / ecdsa
set "ALGORITHM=ed25519"

REM 密钥存储目录
set "SSH_KEY_DIR=%USERPROFILE%\.ssh\new-key"

REM 密钥文件名（留空则根据算法自动命名，如 id_ed25519）
set "KEY_NAME="

REM 是否启用密码短语提示: 1=启用, 0=不启用
set "USE_PASSPHRASE=0"

REM --- 配置结束 ---

