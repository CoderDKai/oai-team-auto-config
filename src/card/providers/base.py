# ==================== 服务商基类 ====================
# 定义信用卡服务商的统一接口

from abc import ABC, abstractmethod
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    PROXY_ENABLED,
    get_proxy_dict,
)


class CardProvider(ABC):
    """信用卡服务商基类

    所有服务商必须实现此接口
    """

    def __init__(self):
        """初始化服务商"""
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建带重试机制的 HTTP Session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # 代理设置
        if PROXY_ENABLED:
            proxy_dict = get_proxy_dict()
            if proxy_dict:
                session.proxies = proxy_dict

        return session

    @abstractmethod
    def query_card_info(self, key_id: str) -> Optional[dict]:
        """查询信用卡信息

        Args:
            key_id: 卡密

        Returns:
            包含信用卡信息的字典，查询失败返回 None
        """
        pass

    def redeem_card(self, key_id: str) -> bool:
        """激活卡密（可选实现）

        Args:
            key_id: 卡密

        Returns:
            是否激活成功
        """
        # 默认实现：不需要激活
        return True

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """服务商名称"""
        pass
