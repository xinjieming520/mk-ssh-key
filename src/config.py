import json
import logging
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .ui import console


logger = logging.getLogger(__name__)

CONFIG_LABELS = {
    "algo": "密钥算法",
    "passphrase": "设置密码",
    "key_password": "密码文本",
    "folder_name": "目录名",
    "key_name": "文件名",
    "comment": "备注信息",
}


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


def save_config(config):
    """保存配置到 config.json"""
    config_path = Path("config.json")
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    logger.info("配置已保存到 config.json")


def get_default_config(config):
    """合并默认配置，避免 config.json 缺少字段时菜单显示为空。"""
    passphrase = config.get("passphrase")
    if passphrase is None:
        passphrase = not config.get("no_passphrase", False)

    return {
        "algo": config.get("algo", "ed25519"),
        "passphrase": passphrase,
        "key_password": config.get("key_password", ""),
        "folder_name": config.get("folder_name", "new-key"),
        "key_name": config.get("key_name"),
        "comment": config.get("comment"),
    }


def format_config_value(key, value):
    if key == "key_password":
        return "[dim]<空>[/]" if not value else "[yellow]已设置 (隐藏)[/]"
    if value is None or value == "":
        return "[dim]<空>[/]"
    if isinstance(value, bool):
        return "[green]true[/]" if value else "[yellow]false[/]"
    return str(value)


def build_config_table(config):
    current_config = get_default_config(config)
    table = Table(
        title="当前配置 (config.json)",
        show_header=True,
        border_style="cyan",
        expand=False,
    )
    table.add_column("字段", style="cyan", no_wrap=True, ratio=1)
    table.add_column("值", overflow="fold", ratio=3)
    for key, value in current_config.items():
        if key == "key_password" and not current_config["passphrase"]:
            continue
        table.add_row(CONFIG_LABELS.get(key, key), format_config_value(key, value))
    return table


def apply_config_to_args(args, config):
    current_config = get_default_config(config)
    args.algo = current_config["algo"]
    args.passphrase = current_config["passphrase"]
    args.key_password = current_config["key_password"]
    args.key_name = current_config["key_name"]
    args.comment = current_config["comment"]
    args.folder_name = current_config["folder_name"]


def edit_config(config):
    """交互式修改 config.json"""
    current_config = get_default_config(config)

    console.print(Panel(
        build_config_table(current_config),
        title="[bold cyan]修改配置[/]",
        border_style="cyan",
        expand=False,
    ))

    algo = Prompt.ask(
        "加密算法",
        choices=["ed25519", "rsa", "ecdsa"],
        default=current_config["algo"],
    )
    passphrase = Confirm.ask(
        "是否设置密码短语",
        default=bool(current_config["passphrase"]),
    )
    key_password = ""
    if passphrase:
        existing_password = current_config["key_password"]
        if existing_password:
            keep_password = Confirm.ask("保留当前已设置的密码短语", default=True)
            if keep_password:
                key_password = existing_password
            else:
                key_password = Prompt.ask("新的密码短语 (直接回车表示不预设)", password=True, default="")
        else:
            key_password = Prompt.ask("密码短语 (直接回车表示不预设)", password=True, default="")

    folder_name = Prompt.ask(
        "~/.ssh 下的子文件夹名",
        default=current_config["folder_name"],
    ).strip() or "new-key"
    key_name = Prompt.ask(
        "密钥文件名 (直接回车表示按算法自动命名)",
        default=current_config["key_name"] or "",
    ).strip() or None
    comment = Prompt.ask(
        "密钥注释",
        default=current_config["comment"] or "",
    ).strip() or None

    new_config = {
        "algo": algo,
        "passphrase": passphrase,
        "key_password": key_password,
        "folder_name": folder_name,
        "key_name": key_name,
        "comment": comment,
    }
    save_config(new_config)
    console.print("[success][✓] 配置已更新并保存到 config.json[/]")
    return new_config
