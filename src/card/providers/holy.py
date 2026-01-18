# ==================== Holy 服务商实现 ====================
# Holy MasterCard 信用卡服务商

from typing import Optional
import requests

from src.core.config import REQUEST_TIMEOUT, USER_AGENT
from src.core.logger import log
from .base import CardProvider


class HolyProvider(CardProvider):
    """Holy MasterCard 服务商"""

    # API 配置
    API_BASE = "https://activate.holymastercard.com"
    QUERY_ENDPOINT = f"{API_BASE}/api/query"
    REDEEM_ENDPOINT = f"{API_BASE}/api/redeem"

    @property
    def provider_name(self) -> str:
        """服务商名称"""
        return "holy"

    def _build_headers(self) -> dict:
        """构建请求头"""
        return {
            "accept": "*/*",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
            "content-type": "application/json",
            "origin": self.API_BASE,
            "referer": f"{self.API_BASE}/",
            "user-agent": USER_AGENT,
        }

    def _query_only(self, key_id: str) -> Optional[dict]:
        """仅查询信用卡信息（内部方法）

        Args:
            key_id: 卡密

        Returns:
            包含信用卡信息的字典，查询失败返回 None
        """
        headers = self._build_headers()
        payload = {"key_id": key_id}

        try:
            response = self.session.post(
                self.QUERY_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data
                else:
                    return None
            else:
                return None

        except Exception:
            return None

    def _redeem_only(self, key_id: str) -> Optional[dict]:
        """仅激活卡密（内部方法）

        Args:
            key_id: 卡密

        Returns:
            包含信用卡信息的字典（如果激活成功），失败返回 None
        """
        headers = self._build_headers()
        payload = {"key_id": key_id}

        try:
            response = self.session.post(
                self.REDEEM_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # 激活成功，返回数据
                    return data
                else:
                    # 激活失败（卡密已被使用等），返回 None
                    return None
            else:
                return None

        except Exception:
            return None

    def query_card_info(self, key_id: str) -> Optional[dict]:
        """查询信用卡信息（先尝试激活，失败后查询）

        Args:
            key_id: 卡密

        Returns:
            包含信用卡信息的字典，查询失败返回 None
        """
        if not key_id:
            log.error("卡密 (key_id) 不能为空")
            return None

        try:
            log.step(f"[Holy] 获取信用卡信息 (key_id: {key_id[:8]}...)")

            # 先尝试激活
            log.step(f"[Holy] 尝试激活卡密...")
            data = self._redeem_only(key_id)

            if data:
                log.success(f"[Holy] 激活成功，获取到卡片信息")
                return data

            # 激活失败，尝试查询
            log.step(f"[Holy] 激活失败，尝试查询已激活的卡片...")
            data = self._query_only(key_id)

            if data:
                log.success(f"[Holy] 查询成功")
                return data
            else:
                log.error("[Holy] 查询失败")
                return None

        except Exception as e:
            log.error(f"[Holy] 获取信息异常: {e}")
            return None

    def redeem_card(self, key_id: str) -> bool:
        """激活卡密

        Args:
            key_id: 卡密

        Returns:
            是否激活成功
        """
        if not key_id:
            log.error("卡密 (key_id) 不能为空")
            return False

        headers = self._build_headers()
        payload = {"key_id": key_id}

        try:
            log.step(f"[Holy] 激活卡密 (key_id: {key_id[:8]}...)")

            response = self.session.post(
                self.REDEEM_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log.success(f"[Holy] 激活成功")
                    return True
                else:
                    error_msg = data.get("error", "未知错误")
                    log.error(f"[Holy] 激活失败: {error_msg}")
                    return False

            else:
                log.error(f"[Holy] 激活失败: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            log.error(f"[Holy] 激活超时")
            return False

        except requests.exceptions.ConnectionError:
            log.error(f"[Holy] 无法连接到服务")
            return False

        except Exception as e:
            log.error(f"[Holy] 激活异常: {e}")
            return False
