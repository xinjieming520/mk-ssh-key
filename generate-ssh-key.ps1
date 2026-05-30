# generate-ssh-key.ps1
# SSH 密钥生成脚本（灵活版）

param(
    [string]$Comment = "",
    [string]$Algorithm = "ed25519",
    [string]$OutputPath = "",
    [switch]$NoPassphrase,
    [switch]$Force
)

# 如果没有指定输出路径，使用默认路径
if (-not $OutputPath) {
    $DefaultDir = Join-Path $env:USERPROFILE ".ssh\myssh\dudu"
    $OutputPath = Join-Path $DefaultDir "id_ed25519"
}

# 分离目录和文件名
$KeyFile = $OutputPath
$SSH_DIR = Split-Path $KeyFile -Parent
$KeyName = Split-Path $KeyFile -Leaf

# 确保目录存在
if (-not (Test-Path $SSH_DIR)) {
    New-Item -ItemType Directory -Path $SSH_DIR -Force | Out-Null
    Write-Host "[✓] 已创建目录: $SSH_DIR" -ForegroundColor Green
}

# 检查密钥文件是否已存在
if ((-not $Force) -and (Test-Path $KeyFile)) {
    Write-Host "[!] 密钥文件已存在: $KeyFile" -ForegroundColor Yellow
    $response = Read-Host "是否覆盖？(y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "[✗] 已取消操作" -ForegroundColor Red
        exit 1
    }
    # 删除旧文件
    Remove-Item $KeyFile -Force -ErrorAction SilentlyContinue
    Remove-Item "$KeyFile.pub" -Force -ErrorAction SilentlyContinue
}

# 获取密码短语
$passphraseStr = ""
if (-not $NoPassphrase) {
    Write-Host ""
    Write-Host "[?] 请输入密码短语（直接回车表示无密码）:" -ForegroundColor Yellow
    Write-Host "   提示：密码短语用于保护私钥，留空则无需密码" -ForegroundColor Gray
    $passphraseStr = Read-Host -Prompt "密码短语"
    
    if ($passphraseStr -ne "") {
        $confirmPass = Read-Host -Prompt "确认密码短语"
        if ($passphraseStr -ne $confirmPass) {
            Write-Host "[✗] 密码不匹配！" -ForegroundColor Red
            exit 1
        }
    }
}

# 显示信息
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SSH 密钥生成工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[→] 算法: $Algorithm" -ForegroundColor White
Write-Host "[→] 目录: $SSH_DIR" -ForegroundColor White
Write-Host "[→] 文件名: $KeyName" -ForegroundColor White
Write-Host "[→] 私钥: $KeyFile" -ForegroundColor White
Write-Host "[→] 公钥: $KeyFile.pub" -ForegroundColor White
if ($Comment) {
    Write-Host "[→] 注释: $Comment" -ForegroundColor White
}
Write-Host ""

# 生成密钥
Write-Host "[...] 正在生成密钥..." -ForegroundColor Cyan

$Arguments = @(
    "-t", $Algorithm,
    "-f", $KeyFile,
    "-N", $passphraseStr
)
if ($Comment) {
    $Arguments += "-C", $Comment
}

try {
    $process = Start-Process -FilePath "ssh-keygen" -ArgumentList $Arguments -NoNewWindow -Wait -PassThru
    
    if ($process.ExitCode -eq 0) {
        Write-Host "[✓] 密钥生成成功！" -ForegroundColor Green
        Write-Host ""
        
        # 修复权限（重要！）
        Write-Host "[...] 正在修复文件权限..." -ForegroundColor Cyan
        icacls $KeyFile /reset > $null 2>&1
        icacls $KeyFile /inheritance:r > $null 2>&1
        icacls $KeyFile /grant:r "${env:USERNAME}:(R,W)" > $null 2>&1
        Write-Host "[✓] 权限已修复" -ForegroundColor Green
        Write-Host ""
        
        # 显示公钥
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  请复制以下公钥到 GitHub/GitLab" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Get-Content "$KeyFile.pub" | ForEach-Object {
            Write-Host $_ -ForegroundColor White
        }
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        
        # 显示指纹
        $fingerprint = ssh-keygen -lf $KeyFile -E sha256 2>$null
        if ($fingerprint) {
            Write-Host ""
            Write-Host "[→] 密钥指纹: $fingerprint" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "[✓] 完成！" -ForegroundColor Green
        Write-Host ""
        Write-Host "提示：如需更新 SSH 配置，请确保 ~/.ssh/config 中的 IdentityFile 指向正确路径：" -ForegroundColor Yellow
        Write-Host "  IdentityFile $KeyFile" -ForegroundColor Cyan
        Write-Host ""
        
        exit 0
    } else {
        Write-Host "[✗] 密钥生成失败，错误代码: $($process.ExitCode)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "[✗] 执行出错: $_" -ForegroundColor Red
    exit 1
}