import argparse
import os
import json
import logging
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.theme import Theme

# 配置日志
logging.basicConfig(
    filename="ssh_key_gen.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "path": "underline blue",
})

console = Console(theme=custom_theme)

def load_config():
    """从 config.json 加载配置"""
    config_path = Path("config.json")
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            logger.info("成功从 config.json 加载配置")
            return config
        except Exception as e:
            logger.error(f"读取 config.json 失败: {e}")
            console.print(f"[warning][!] 无法读取 config.json: {e}[/]")
    return {}

def get_base_ssh_dir():
    """返回系统默认的 SSH 根目录 (~/.ssh)"""
    return Path.home() / ".ssh"

def fix_permissions(key_path):
    """修复 Windows 下私钥文件的权限"""
    if os.name == 'nt':
        try:
            logger.info(f"正在修复权限: {key_path}")
            # 重置权限并禁用继承，只允许当前用户读取
            username = os.environ.get("USERNAME")
            subprocess.run(["icacls", str(key_path), "/reset"], capture_output=True, check=True)
            subprocess.run(["icacls", str(key_path), "/inheritance:r"], capture_output=True, check=True)
            subprocess.run(["icacls", str(key_path), "/grant:r", f"{username}:(R,W)"], capture_output=True, check=True)
            logger.info("权限修复成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"权限修复失败: {e}")
            return False
    return True

def generate_key(algo, comment, output_path, passphrase, force=False):
    output_path = Path(output_path).expanduser().resolve()
    pub_key_path = output_path.with_suffix(".pub")

    # 确保目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 检查冲突
    if not force and output_path.exists():
        console.print(f"[warning][!] 密钥文件已存在: {output_path}[/]")
        if not Confirm.ask("是否覆盖？"):
            logger.info(f"操作取消 (文件已存在): {output_path}")
            console.print("[error][✗] 操作已取消[/]")
            sys.exit(0)
        
        # 删除旧文件
        output_path.unlink(missing_ok=True)
        pub_key_path.unlink(missing_ok=True)

    # 构建命令
    cmd = ["ssh-keygen", "-t", algo, "-f", str(output_path), "-N", passphrase]
    if comment:
        cmd.extend(["-C", comment])

    console.print(f"\n[info][...] 正在为 {comment or '无注释'} 生成 {algo} 密钥...[/]")
    logger.info(f"启动 ssh-keygen (算法: {algo}, 路径: {output_path})")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("密钥生成成功")
            console.print("[success][✓] 密钥生成成功！[/]")
            console.print(f"[success][✓] 私钥路径: {output_path}[/]")
            console.print(f"[success][✓] 公钥路径: {pub_key_path}[/]")
            
            # 修复权限
            console.print("[info][...] 正在修复文件权限...[/]")
            if fix_permissions(output_path):
                console.print("[success][✓] 权限已修复[/]")
            else:
                console.print("[warning][!] 权限修复失败，请手动检查。[/]")

            # 显示公钥
            if pub_key_path.exists():
                pub_content = pub_key_path.read_text().strip()
                console.print("\n")
                console.print(Panel(
                    f"[info]{pub_content}[/]",
                    title="[yellow]公钥内容 (请复制到 GitHub/GitLab)[/]",
                    border_style="cyan",
                    expand=True
                ))
           
            # 显示指纹
            fp_res = subprocess.run(["ssh-keygen", "-lf", str(output_path)], capture_output=True, text=True)
            if fp_res.returncode == 0:
                fingerprint = fp_res.stdout.strip()
                logger.info(f"密钥指纹: {fingerprint}")
                console.print(Panel(
                    f"[info]{fingerprint}[/]",
                    title="[yellow]密钥指纹 (添加成功后可对比一致性)[/]",
                    border_style="cyan",
                    expand=True
                ))

        else:
            err_msg = result.stderr.strip()
            logger.error(f"ssh-keygen 失败: {err_msg}")
            console.print(f"[error][✗] 密钥生成失败: {err_msg}[/]")
            sys.exit(1)
    except Exception as e:
        logger.exception("生成过程中发生未预期异常")
        console.print(f"[error][✗] 执行出错: {e}[/]")
        sys.exit(1)

def main():
    config = load_config()
    
    parser = argparse.ArgumentParser(description="SSH 密钥生成工具 (Python 版)")
    parser.add_argument("--algo", default=config.get("algo", "ed25519"), choices=["ed25519", "rsa", "ecdsa"], help="加密算法")
    parser.add_argument("--comment", default=config.get("comment"), help="密钥注释 (建议填写邮箱)")
    parser.add_argument("--folder-name", default=config.get("folder_name", "new-key"), help="~/.ssh 下的子文件夹名")
    parser.add_argument("--key-name", default=config.get("key_name"), help="密钥文件名 (默认根据算法命名)")
    parser.add_argument("--no-passphrase", action="store_true", default=config.get("no_passphrase", False), help="不使用密码短语")
    parser.add_argument("--key-password", default=config.get("key_password"), help="自动填充的密码短语")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有密钥")

    
    args = parser.parse_args()

    from rich.align import Align
    console.print(Panel(Align.center("[bold]SSH 密钥生成工具[/]"), style="cyan", border_style="cyan", expand=True))

    # 确定路径
    base_dir = get_base_ssh_dir()
    target_dir = base_dir / args.folder_name
    target_name = args.key_name if args.key_name else f"id_{args.algo}"
    target_path = target_dir / target_name
    comment = args.comment or "my-email@example.com"

    # 显示预览配置
    from rich.table import Table
    table = Table(title="当前密钥配置", show_header=False, border_style="cyan")    
    table.add_row("加密算法", args.algo)
    
    # 密码状态
    if args.no_passphrase:
        pass_status = "不使用"
    elif args.key_password:
        pass_status = "已预设 (从配置加载)"
    else:
        pass_status = "生成时手动输入"
        
    table.add_row("使用密码", pass_status)
    table.add_row("密钥名字", target_name)
    table.add_row("公钥注释", comment)
    table.add_row("输出目录", str(target_dir))   
    table.add_row("完整路径", str(target_path))
    
    console.print(table)
    console.print("")

    if not Confirm.ask("[warning]是否确认以上配置并继续？[/]"):
        logger.info("用户取消操作 (确认阶段)")
        console.print("[error][✗] 操作已取消[/]")
        sys.exit(0)

    passphrase = ""
    if not args.no_passphrase:
        if args.key_password:
            passphrase = args.key_password
            console.print(f"\n[info][✓] 使用预设的密码短语[/]")
        else:
            console.print("\n[info][?] 请输入密码短语 (直接回车表示无密码):[/]")
            passphrase = Prompt.ask("密码短语", password=True)
            if passphrase:
                confirm = Prompt.ask("确认密码短语", password=True)
                if passphrase != confirm:
                    logger.warning("密码短语二次确认不匹配")
                    console.print("[error][✗] 密码不匹配！[/]")
                    sys.exit(1)

    # 执行生成
    generate_key(args.algo, comment, target_path, passphrase, args.force)

if __name__ == "__main__":
    main()
