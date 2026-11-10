"""配置加载：从.env或环境变量读取API配置。"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    timeout: int = 60


def load_config() -> Config:
    """加载配置，缺少API Key时抛出明确错误。"""
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "未找到 DEEPSEEK_API_KEY，请在项目根目录创建 .env 文件：\n"
            "DEEPSEEK_API_KEY=你的密钥"
        )
    return Config(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )
