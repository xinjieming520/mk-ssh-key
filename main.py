import logging

from src.app import main
from src.logging_config import setup_logging
from src.ui import console


logger = logging.getLogger(__name__)


if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[warning][!] 已取消操作，程序已退出。[/]")
        logger.info("用户通过 Ctrl+C 退出程序")
