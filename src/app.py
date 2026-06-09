import argparse
import logging

from rich.console import Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .config import apply_config_to_args, build_config_table, edit_config, load_config
from .ssh_tools import generate_key, test_connection
from .system_utils import deep_fix_permissions, get_base_ssh_dir, get_version
from .ui import console


logger = logging.getLogger(__name__)


def build_parser(config):
    parser = argparse.ArgumentParser(description="SSH 密钥生成及测试工具")
    parser.add_argument("--algo", default=config.get("algo", "ed25519"), choices=["ed25519", "rsa", "ecdsa"], help="加密算法")
    parser.add_argument("--comment", default=config.get("comment"), help="密钥注释 (建议填写邮箱)")
    parser.add_argument("--folder-name", default=config.get("folder_name", "new-key"), help="~/.ssh 下的子文件夹名")
    parser.add_argument("--key-name", default=config.get("key_name"), help="密钥文件名 (默认根据算法命名)")
    parser.add_argument("--no-passphrase", action="store_true", default=config.get("no_passphrase", False), help="不使用密码短语")
    parser.add_argument("--key-password", default=config.get("key_password"), help="自动填充的密码短语")
    parser.add_argument("--force", action="store_true", help="强制覆盖现有密钥")
    return parser


def handle_generate_key(args):
    base_dir = get_base_ssh_dir()
    target_dir = base_dir / args.folder_name
    target_name = args.key_name if args.key_name else f"id_{args.algo}"
    target_path = target_dir / target_name
    comment = args.comment or "my-email@example.com"

    table = Table(title="当前密钥配置", show_header=False, border_style="cyan", expand=False)
    table.add_column(justify="center", style="cyan")
    table.add_column(justify="left")

    table.add_row("加密算法", args.algo)

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
        return

    passphrase = ""
    if not args.no_passphrase:
        if args.key_password:
            passphrase = args.key_password
            console.print("\n[info][✓] 使用预设的密码短语[/]")
        else:
            console.print("\n[info][?] 请输入密码短语 (直接回车表示无密码):[/]")
            passphrase = Prompt.ask("密码短语", password=True)
            if passphrase:
                confirm = Prompt.ask("确认密码短语", password=True)
                if passphrase != confirm:
                    logger.warning("密码短语二次确认不匹配")
                    console.print("[error][✗] 密码不匹配！[/]")
                    input("\n按回车键继续...")
                    return

    generate_key(args.algo, comment, target_path, passphrase, args.force)


def main():
    config = load_config()
    parser = build_parser(config)
    args = parser.parse_args()

    git_v = get_version(["git", "--version"])
    ssh_v = get_version(["ssh", "-V"])

    git_info = f"Git: [success]{git_v}[/]" if git_v else "Git: [error]未安装[/]"
    ssh_info = f"OpenSSH: [success]{ssh_v.split(',')[0]}[/]" if ssh_v else "OpenSSH: [error]未安装[/]"

    while True:
        console.clear()
        header_text = Text.from_markup(
            f"[bold]SSH 密钥管理工具[/]\n\n[dim]依赖检测：\n  {git_info} | {ssh_info}[/]"
        )
        menu_text = Text.from_markup(
            "\n[bold cyan]1.[/] 生成 SSH 密钥\n"
            "[bold cyan]2.[/] 测试 SSH 连接\n"
            "[bold cyan]3.[/] 深度修复权限\n"
            "[bold cyan]4.[/] 修改配置\n"
            "[bold cyan]0.[/] 退出程序"
        )
        console.print(Panel(
            Group(header_text, build_config_table(config), menu_text),
            style="cyan",
            border_style="cyan",
            expand=False,
        ))

        choice = Prompt.ask("\n请选择操作", choices=["1", "2", "3", "4", "0"], default="1")

        if choice == "1":
            handle_generate_key(args)
            input("\n操作完成，按回车键返回菜单...")

        elif choice == "2":
            test_connection(args.folder_name, args.key_password, args.no_passphrase)
            input("\n测试完成，按回车键返回菜单...")

        elif choice == "3":
            deep_fix_permissions()
            input("\n修复完成，按回车键返回菜单...")

        elif choice == "4":
            config = edit_config(config)
            apply_config_to_args(args, config)
            input("\n配置完成，按回车键返回菜单...")

        elif choice == "0":
            console.print("[info]感谢使用，再见！[/]")
            break
