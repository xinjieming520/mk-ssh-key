import logging
import os
import subprocess
from pathlib import Path

from rich.panel import Panel

from .ui import console


logger = logging.getLogger(__name__)


def run_command(command):
    """运行系统命令"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {command}")
        logger.error(f"错误输出: {e.stderr}")
        raise e


def get_base_ssh_dir():
    """返回系统默认的 SSH 根目录 (~/.ssh)"""
    return Path.home() / ".ssh"


def get_version(command):
    """获取命令的版本号"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout.strip() or result.stderr.strip()
        version = output.split("\n")[0].replace("git version ", "").replace("OpenSSH_", "")
        return version
    except Exception:
        return None


def deep_fix_permissions():
    """深度权限修复函数"""
    if os.name != "nt":
        console.print("[warning][!] 深度权限修复仅支持 Windows 系统[/]")
        return

    console.print(Panel.fit(
        "[bold cyan]🔐 正在执行深度权限修复...[/]",
        border_style="cyan",
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
                    console.print(f"[red]⚠️ 权限修复失败: {path} - {e}[/]")
                    fail_count += 1

    console.print("\n[bold cyan]🔑 正在修复 SSH 敏感文件权限...[/]\n")
    username = os.environ.get("USERNAME")
    ssh_files = []

    if os.path.exists(config_file):
        ssh_files.append(config_file)

    if os.path.exists(ssh_base):
        for root, dirs, files in os.walk(ssh_base):
            for file in files:
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

    result_panel = Panel.fit(
        f"[bold green]深度修复完成！[/]\n\n"
        f"[green]✅ 成功: {success_count}[/]\n"
        f"[red]❌ 失败: {fail_count}[/]" if fail_count > 0 else f"[green]✅ 成功: {success_count}[/]",
        border_style="green",
    )
    console.print(result_panel)

