# SSH 密钥生成工具

用于在 Windows 系统上快速生成 SSH 密钥，支持多种加密算法，并提供安全的文件权限修复。

## 📁 目录结构

```
ssh-key/
├── README.md               # 本说明文档
├── run.bat                 # 快捷启动脚本（支持参数）
├── config.local.bat        # 本地个人配置文件（可选）
└── generate-ssh-key.ps1    # 核心密钥生成脚本 (PowerShell)
```

## 🚀 快速开始

### 方式一：使用 `run.bat` (推荐)

直接双击 `run.bat` 使用默认配置生成密钥。或者在命令行中灵活使用参数：

```batch
# 生成无密码密钥
run.bat --no-passphrase

# 自定义目录和注释
run.bat --dir "C:\MyKeys" --comment "user@work.com"

# 使用 RSA 算法并自动命名 (生成 id_rsa)
run.bat --algo rsa
```

**`run.bat` 命令行参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--no-passphrase` | 不设置密码短语 | - |
| `--dir <路径>` | 指定密钥存储目录 | `--dir "D:\keys"` |
| `--name <文件名>` | 指定密钥文件名 | `--name "github_key"` |
| `--comment <注释>` | 指定密钥注释（通常填邮箱） | `--comment "mail@abc.com"` |
| `--algo <算法>` | 指定算法 (ed25519/rsa/ecdsa) | `--algo rsa` |

---

### 方式二：使用 `config.local.bat` (持久化配置)

如果你不想每次都输入参数，可以修改 `config.local.bat` 来固化你的个人偏好（如常用邮箱、算法等）。脚本会自动加载此文件中的变量。

---

### 方式三：PowerShell 命令行运行

如果你熟悉 PowerShell，可以直接调用核心脚本：

```powershell
# 基本用法
.\generate-ssh-key.ps1 -Comment "user@example.com" -Algorithm ed25519

# 无密码、强制覆盖
.\generate-ssh-key.ps1 -NoPassphrase -Force
```

## 📖 PowerShell 参数详解

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `-Comment` | 密钥注释 | 任意字符串 | 空 |
| `-Algorithm` | 加密算法 | `rsa`, `ed25519`, `ecdsa` | `ed25519` |
| `-OutputPath` | 完整输出路径 | 文件路径 | `~/.ssh/new-key/id_<algo>` |
| `-NoPassphrase` | 不设置密码短语 | 开关 | 默认会有交互提示 |
| `-Force` | 强制覆盖现有文件 | 开关 | 默认询问 |

## 🔐 算法建议

| 算法 | 位数 | 特点 | 推荐场景 |
|------|------|------|----------|
| **Ed25519** | 256位 | 最新、最安全、体积小、性能好 | ✅ **首选推荐** |
| RSA | 4096位 | 兼容性极强（支持旧服务器） | 旧系统兼容 |
| ECDSA | 521位 | NIST 标准 | 特定合规场景 |

## 📂 生成的密钥文件

默认情况下，密钥保存在 `~/.ssh/new-key/` 目录下：

*   `id_ed25519` / `id_rsa`: **私钥**（绝对不要泄露！）
*   `id_ed25519.pub` / `id_rsa.pub`: **公钥**（用于上传到 GitHub/GitLab）

## 🔑 后续步骤

### 1. 添加到 SSH Agent (可选但推荐)
```powershell
# 启动服务
Start-Service ssh-agent
# 添加私钥
ssh-add ~/.ssh/new-key/id_ed25519
```

### 2. 配置 SSH Config
建议在 `~/.ssh/config` 中添加以下配置，以便 Git 自动使用新密钥：
```text
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/new-key/id_ed25519
```

## ⚠️ 安全与注意事项

1.  **密码短语输入**：在生成过程中输入密码短语时，屏幕**不会显示任何字符**，这是正常的安全保护。
2.  **文件权限**：脚本会自动运行 `icacls` 修复私钥权限（仅限当前用户读写），确保 SSH 客户端不会因为“权限过高”而拒绝使用。
3.  **禁止执行脚本**：如果遇到“禁止执行脚本”错误，请以管理员身份运行：
    `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## 📝 帮助命令
```powershell
Get-Help .\generate-ssh-key.ps1 -Full
```
