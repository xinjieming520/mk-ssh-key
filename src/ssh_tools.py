import logging
import subprocess
import sys
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm

from .ui import console


logger = logging.getLogger(__name__)


def generate_key(algo, comment, output_path, passphrase, force=False):
    output_path = Path(output_path).expanduser().resolve()
    pub_key_path = output_path.with_suffix(".pub")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not force and output_path.exists():
        console.print(f"[warning][!] 密钥文件已存在: {output_path}[/]")
        if not Confirm.ask("是否覆盖？"):
            logger.info(f"操作取消 (文件已存在): {output_path}")
            console.print("[error][✗] 操作已取消[/]")
            sys.exit(0)

        output_path.unlink(missing_ok=True)
        pub_key_path.unlink(missing_ok=True)

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

            if pub_key_path.exists():
                pub_content = pub_key_path.read_text().strip()
                console.print("\n")
                console.print(Panel(
                    f"[info]{pub_content}[/]",
                    title="[yellow]公钥内容 (请复制到 GitHub/GitLab)[/]",
                    border_style="cyan",
                    expand=True,
                ))

            fp_res = subprocess.run(["ssh-keygen", "-lf", str(output_path)], capture_output=True, text=True)
            if fp_res.returncode == 0:
                fingerprint = fp_res.stdout.strip()
                logger.info(f"密钥指纹: {fingerprint}")
                console.print(Panel(
                    f"[info]{fingerprint}[/]",
                    title="[yellow]密钥指纹 (添加成功后可对比一致性)[/]",
                    border_style="cyan",
                    expand=True,
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


def test_connection(folder_name, key_password=None, passphrase=False):
    """测试 SSH 连接"""
    host = folder_name
    console.print(f"\n[info][...] 正在准备连接 {host}...[/]")

    cmd = ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-T", f"git@{host}"]

    console.print(Panel(
        f"[yellow]执行命令:[/] [cyan]{' '.join(cmd)}[/]\n"
        f"[dim]配置状态: {'需要输入密码' if passphrase else '无密码'}[/]",
        title="连接测试",
        border_style="cyan",
        expand=True,
    ))

    if not Confirm.ask("[warning]是否继续？[/]"):
        return

    try:
        if not passphrase:
            with console.status("[info]正在建立连接...[/]", spinner="dots"):
                result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                console.print(f"\n[info]测试结果:[/]\n{result.stdout.strip()}")
            if result.stderr:
                console.print(f"\n[info]附加信息:[/]\n{result.stderr.strip()}")
        else:
            console.print("[info]------ SSH 连接输出开始 ------[/]")
            result = subprocess.run(cmd)
            console.print("[info]------ SSH 连接输出结束 ------[/]")

        if result.returncode in [0, 1]:
            console.print(f"\n[success][✓] 连接测试完成 (返回码: {result.returncode})[/]")
        else:
            console.print(f"\n[error][✗] 连接失败 (返回码: {result.returncode})[/]")
            console.print("[warning][!] 如果看到 'Permission denied'，强烈建议执行菜单中的 [bold]‘深度修复权限’[/] 后再试。[/]")
            if passphrase:
                console.print("[dim]提示：请同时检查密码是否正确或密钥是否已添加到 Agent。[/]")
    except Exception as e:
        console.print(f"[error][✗] 测试出错: {e}[/]")
