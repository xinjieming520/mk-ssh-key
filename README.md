# SSH 密钥生成工具

一个基于 Python 和 `uv` 的现代化 SSH 密钥生成工具，提供美观的界面、安全的交互和自动化的权限管理。

## ✨ 特性

- **环境隔离**：使用 `uv` 自动管理 Python 环境和依赖，无需手动配置。
- **安全第一**：
  - 密码短语输入时自动遮蔽（无回显）。
  - **自动修复 Windows 权限**：生成私钥后自动调用 `icacls` 修复文件权限，确保 SSH 客户端可直接使用。
- **灵活配置**：支持 `config.json` 持久化配置，并支持命令行参数实时覆盖。
- **操作日志**：所有生成记录、错误信息及密钥指纹都会记录在 `log/ssh_key_gen.log` 中。

## 🚀 快速开始

### 1. 安装 uv (如果尚未安装)

访问 [uv 官网](https://docs.astral.sh/uv/getting-started/installation/) 或在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 运行工具

在项目目录下，直接使用 `uv` 运行：

```powershell
# 使用默认配置 (Ed25519 算法，保存到 ~/.ssh/new-key/)
uv run main.py
```

### 3. 配置文件 (config.json)

在项目根目录修改 `config.json` 来持久化你的个人偏好。如果存在此文件，脚本将自动加载其中的设置作为默认值。

**示例 `config.json`：**

```json
{
    "comment": "xxx@gmail.com",
    "algo": "ed25519",
    "folder_name": "new-key",
    "key_name": null,
    "no_passphrase": false,
    "key_password": "your-password-here"
}
```

- `folder_name`: 会在系统 `~/.ssh/` 目录下创建此名称的子文件夹。
- `key_name`: 密钥的文件名（留空则根据算法自动命名）。
- `key_password`: 预设密钥密码。当 `no_passphrase` 为 `false` 时，程序将自动使用此密码而不再询问。

### 4. 命令行参数

你可以通过参数灵活控制生成行为：

```powershell
# 指定邮箱注释和无密码生成
uv run main.py --comment "your-email@example.com" --no-passphrase

# 指定子文件夹和自定义文件名
uv run main.py --algo rsa --folder-name "work-git" --key-name "id_rsa_company" --key-password "mypassword"

# 查看完整帮助
uv run main.py --help
```

| 参数 | 说明 | 对应配置字段 |
|------|------|--------------|
| `--algo` | 加密算法 (`ed25519`, `rsa`, `ecdsa`) | `algo` |
| `--comment` | 密钥注释 (通常填邮箱) | `comment` |
| `--folder-name` | `~/.ssh/` 下的子文件夹名 | `folder_name` |
| `--key-name` | 密钥文件名 | `key_name` |
| `--no-passphrase` | 不使用密码短语 | `no_passphrase` |
| `--key-password` | 自动填充的密码短语 | `key_password` |
| `--force` | 强制覆盖现有文件 | - |

## 📂 生成的密钥

默认存储在：`%USERPROFILE%\.ssh\{folder_name}\`

- `id_ed25519`: **私钥** (已自动加锁，仅限当前用户读取)
- `id_ed25519.pub`: **公钥** (复制此内容到 GitHub/GitLab)

## 🔑 后续步骤

### 添加到 SSH Agent

```powershell
Start-Service ssh-agent
ssh-add ~/.ssh/new-key/id_ed25519
```

### 配置 SSH Config

建议修改 `~/.ssh/config`，以便 Git 自动识别不同文件夹下的密钥：

```text
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/new-key/id_ed25519
```

## 🛠️ 常见问题

- **提示找不到 `ssh-keygen`？** 请确保已安装 Git 或 OpenSSH。
- **查看日志**：所有操作历史和密钥指纹均可在 `log/ssh_key_gen.log` 中找到。
