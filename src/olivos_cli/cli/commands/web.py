"""
web 命令实现
"""

import webbrowser
from pathlib import Path

try:
    import uvicorn
except ImportError:
    uvicorn = None

from ...core import ConfigManager, get_logger
from ...core.exceptions import OlivOSCLIError
from ...web.app import app, set_config_manager

logger = get_logger()


def cmd_web(config_manager: ConfigManager, args) -> int:
    """启动 WebUI"""
    if uvicorn is None:
        logger.error_print("未找到 uvicorn 模块，请重新安装 olivos-cli")
        logger.info_print("尝试: pip install olivos-cli[web]")
        return 1

    host = args.host
    port = args.port
    
    set_config_manager(config_manager)

    url = f"http://{host}:{port}"
    logger.success(f"WebUI 正在启动: {url}")

    if not args.no_browser:
        logger.info_print("正在打开浏览器...")
        import threading
        import time
        
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(url)
            
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        logger.info_print("WebUI 已停止")
    except Exception as e:
        logger.error_print(f"WebUI 启动失败: {e}")
        return 1

    return 0
