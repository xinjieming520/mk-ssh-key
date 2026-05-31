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

def run_command(command):
    """运行系统命令"""
    try:
        # 在 Windows 上使用 shell=True 以支持复杂的命令字符串
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {command}")
        logger.error(f"错误输出: {e.stderr}")
        raise e

def get_base_ssh_dir():
    """返回系统默认的 SSH 根目录 (~/.ssh)"""
    return Path.home() / ".ssh"

def deep_fix_permissions():
    """深度权限修复函数"""
    if os.name != 'nt':
        console.print("[warning][!] 深度权限修复仅支持 Windows 系统[/]")
        return

    console.print(Panel.fit(
        "[bold cyan]🔐 正在执行深度权限修复...[/]",
        border_style="cyan"
    ))
    console.print()

    config_file = "config.json"
    ssh_base = str(get_base_ssh_dir())
    
    target_paths = [config_file, ssh_base]
    success_count = 0
    fail_count = 0

    for path in target_paths:
        if os.path.exists(path):
            with console.status(f"[dim]处理中: {path}[/]", spinner="dots"):
                try:
                    username = os.environ.get("USERNAME")
                    if os.path.isdir(path):
                        run_command(f'takeown /f "{path}" /r /d y')
                        run_command(f'icacls "{path}" /reset /t /c /q')
                        run_command(f'icacls "{path}" /grant:r {username}:(OI)(CI)F /t /c')
                    else:
                        run_command(f'takeown /f "{path}"')
                        run_command(f'icacls "{path}" /reset /q')
                        run_command(f'icacls "{path}" /grant:r {username}:F /c')
                    success_count += 1
                except Exception as e:
                    console.print(f"[red]⚠️  权限修复失败: {path} - {e}[/]")
                    fail_count += 1

    console.print(f"\n[bold cyan]🔑 正在修复 SSH 敏感文件权限...[/]\n")
    username = os.environ.get("USERNAME")
    ssh_files = []

    if os.path.exists(config_file):
        ssh_files.append(config_file)

    if os.path.exists(ssh_base):
        for root, dirs, files in os.walk(ssh_base):
            for file in files:
                # 匹配 id_rsa, id_ed25519 等私钥文件
                if file.startswith("id_") and not file.endswith(".pub"):
                    ssh_files.append(os.path.join(root, file))

    for file_path in ssh_files:
        try:
            run_command(f'takeown /f "{file_path}"')
            run_command(f'icacls "{file_path}" /inheritance:r')
            run_command(f'icacls "{file_path}" /grant:r {username}:F')
            run_command(f'icacls "{file_path}" /remove:g "CREATOR OWNER" /q 2>nul')
            run_command(f'icacls "{file_path}" /remove:g "SYSTEM" /q 2>nul')
            run_command(f'icacls "{file_path}" /remove:g "Administrators" /q 2>nul')
            run_command(f'icacls "{file_path}" /remove:g "Users" /q 2>nul')
            console.print(f"  [green]✅[/] [dim]{os.path.basename(file_path)}[/]")
            success_count += 1
        except Exception as e:
            console.print(f"  [yellow]⚠️  {os.path.basename(file_path)} 修复失败: {e}[/]")
            fail_count += 1

    # 显示修复结果摘要
    console.print()
    result_panel = Panel.fit(
        f"[bold green]深度修复完成！[/]\n\n"
        f"[green]✅ 成功: {success_count}[/]\n"
        f"[red]❌ 失败: {fail_count}[/]" if fail_count > 0 else f"[green]✅ 成功: {success_count}[/]",
        border_style="green"
    )
    console.print(result_panel)

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
            
            console.print("\n[info]提示: 如果后续连接测试失败，请尝试使用主菜单中的 [bold]‘深度修复权限’[/] 功能。[/]")

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

def test_connection(folder_name, key_password=None, no_passphrase=False):
    """测试 SSH 连接"""
    host = folder_name
    console.print(f"\n[info][...] 正在准备连接 {host}...[/]")
    
    # 构建 ssh 命令
    cmd = ["ssh", "-T", f"git@{host}"]
    
    console.print(Panel(
        f"[yellow]执行命令:[/] [cyan]ssh -T git@{host}[/]\n"
        f"[dim]配置状态: {'无密码' if no_passphrase else '需要输入密码'}[/]", 
        title="连接测试", border_style="cyan", expand=True
    ))
    
    if not Confirm.ask("[warning]是否继续？[/]"):
        return

    try:
        if no_passphrase:
            # 无密码模式：保持美观的加载动画并捕获输出
            with console.status("[info]正在建立连接...[/]", spinner="dots"):
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 状态动画结束后清除并显示结果
            if result.stdout:
                console.print(f"\n[info]测试结果:[/]\n{result.stdout.strip()}")
            if result.stderr:
                console.print(f"\n[info]附加信息:[/]\n{result.stderr.strip()}")
        else:
            # 有密码模式：为了支持交互式输入密码，不能捕获输出，也不使用加载动画
            console.print("[info]------ SSH 连接输出开始 ------[/]")
            # 直接运行，不捕获输出，允许用户在终端输入密码
            result = subprocess.run(cmd)
            console.print("[info]------ SSH 连接输出结束 ------[/]")

        if result.returncode in [0, 1]:
            # ssh -T git@github.com 成功时通常返回 1 并显示欢迎信息
            console.print(f"\n[success][✓] 连接测试完成 (返回码: {result.returncode})[/]")
        else:
            console.print(f"\n[error][✗] 连接失败 (返回码: {result.returncode})[/]")
            console.print("[warning][!] 如果看到 'Permission denied'，强烈建议执行菜单中的 [bold]‘深度修复权限’[/] 后再试。[/]")
            if not no_passphrase:
                console.print("[dim]提示：请同时检查密码是否正确或密钥是否已添加到 Agent。[/]")
    except Exception as e:
        console.print(f"[error][✗] 测试出错: {e}[/]")

def get_version(command):
    """获取命令的版本号"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout.strip() or result.stderr.strip()
        # 提取第一行并简单清理
        version = output.split('\n')[0].replace("git version ", "").replace("OpenSSH_", "")
        return version
    except Exception:
        return None

def main():
    config = load_config()
    
    parser = argparse.ArgumentParser(description="SSH 密钥生成及测试工具")
    parser.add_argument("--algo", default=config.get("algo", "ed25519"), choices=["ed25519", "rsa", "ecdsa"], help="加密算法")
    parser.add_argument("--comment", default=config.get("comment"), help="密钥注释 (建议填写邮箱)")
    parser.add_argument("--folder-name", default=config.get("folder_name", "new-key"), help="~/.ssh 下的子文件夹名")
    parser.add_argument("--key-name", default=config.get("key_name"), help="密钥文件名 (默认根据算法命名)")
    parser.add_argument("--no-passphrase", action="store_true", default=config.get("no_passphrase", False), help="不使用密码短语")
    parser.add_argument("--key-password", default=config.get("key_password"), help="自动填充的密码短语")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有密钥")

    args = parser.parse_args()

    from rich.align import Align
    from rich.text import Text
    
    # 预先检测版本
    git_v = get_version(["git", "--version"])
    ssh_v = get_version(["ssh", "-V"])
    
    git_info = f"Git: [success]{git_v}[/]" if git_v else "Git: [error]未安装[/]"
    ssh_info = f"OpenSSH: [success]{ssh_v.split(',')[0]}[/]" if ssh_v else "OpenSSH: [error]未安装[/]"

    while True:
        console.clear()
        header_text = Text.from_markup(
            f"[bold]SSH 密钥管理工具[/]\n[dim]依赖检测：{git_info} | {ssh_info}[/]", 
            justify="center"
        )
        console.print(Panel(header_text, style="cyan", border_style="cyan", expand=True))
        
        console.print("\n[bold cyan]1.[/] 生成 SSH 密钥")
        console.print("[bold cyan]2.[/] 测试 SSH 连接")
        console.print("[bold cyan]3.[/] 深度修复权限")
        console.print("[bold cyan]0.[/] 退出程序")
        
        choice = Prompt.ask("\n请选择操作", choices=["1", "2", "3", "0"], default="1")
        
        if choice == "1":
            # ... (no changes here, just keeping it for context in replace)
            base_dir = get_base_ssh_dir()
            target_dir = base_dir / args.folder_name
            target_name = args.key_name if args.key_name else f"id_{args.algo}"
            target_path = target_dir / target_name
            comment = args.comment or "my-email@example.com"

            # 显示预览配置
            from rich.table import Table
            table = Table(title="当前密钥配置", show_header=False, border_style="cyan", expand=True)
            table.add_column(justify="center", style="cyan")
            table.add_column(justify="left")
            
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

            if not Confirm.ask("[warning]是否确认以上配置并开始生成？[/]"):
                continue

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
                            input("\n按回车键继续...")
                            continue

            # 执行生成
            generate_key(args.algo, comment, target_path, passphrase, args.force)
            input("\n操作完成，按回车键返回菜单...")

        elif choice == "2":
            test_connection(args.folder_name, args.key_password, args.no_passphrase)
            input("\n测试完成，按回车键返回菜单...")

        elif choice == "3":
            deep_fix_permissions()
            input("\n修复完成，按回车键返回菜单...")
            
        elif choice == "0":
            console.print("[info]感谢使用，再见！[/]")
            break

if __name__ == "__main__":
    main()
