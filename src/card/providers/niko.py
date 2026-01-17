# ==================== Niko 服务商实现 ====================
# Niko Mercury 信用卡服务商

from typing import Optional
import requests

from src.core.config import REQUEST_TIMEOUT, USER_AGENT
from src.core.logger import log
from .base import CardProvider


class NikoProvider(CardProvider):
    """Niko Mercury 服务商"""

    # API 配置
    API_BASE = "https://mercury.wxie.de"
    QUERY_ENDPOINT = f"{API_BASE}/api/keys/query"
    REDEEM_ENDPOINT = f"{API_BASE}/api/keys/redeem"

    @property
    def provider_name(self) -> str:
        """服务商名称"""
        return "niko"

    def _build_headers(self) -> dict:
        """构建请求头"""
        return {
            "accept": "*/*",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
            "content-type": "application/json",
            "origin": self.API_BASE,
            "referer": f"{self.API_BASE}/redeem",
            "user-agent": USER_AGENT,
        }

    def query_card_info(self, key_id: str) -> Optional[dict]:
        """查询信用卡信息

        Args:
            key_id: 卡密

        Returns:
            包含信用卡信息的字典，查询失败返回 None
        """
        if not key_id:
            log.error("卡密 (key_id) 不能为空")
            return None

        headers = self._build_headers()
        payload = {"key_id": key_id}

        try:
            log.step(f"[Niko] 查询信用卡信息 (key_id: {key_id[:8]}...)")

            response = self.session.post(
                self.QUERY_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log.success(f"[Niko] 查询成功")
                    return data
                else:
                    log.error("[Niko] 查询失败: API 返回 success=false")
                    return None

            elif response.status_code == 404:
                log.error(f"[Niko] 卡密无效或不存在 (HTTP 404)")
                return None

            elif response.status_code == 400:
                log.error(f"[Niko] 请求参数错误 (HTTP 400)")
                return None

            else:
                log.error(f"[Niko] 查询失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            log.error(f"[Niko] 查询超时")
            return None

        except requests.exceptions.ConnectionError:
            log.error(f"[Niko] 无法连接到服务")
            return None

        except Exception as e:
            log.error(f"[Niko] 查询异常: {e}")
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
            log.step(f"[Niko] 激活卡密 (key_id: {key_id[:8]}...)")

            response = self.session.post(
                self.REDEEM_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    log.success(f"[Niko] 激活成功")
                    return True
                else:
                    error_msg = data.get("error", "未知错误")
                    log.error(f"[Niko] 激活失败: {error_msg}")
                    return False

            else:
                log.error(f"[Niko] 激活失败: HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            log.error(f"[Niko] 激活超时")
            return False

        except requests.exceptions.ConnectionError:
            log.error(f"[Niko] 无法连接到服务")
            return False

        except Exception as e:
            log.error(f"[Niko] 激活异常: {e}")
            return False
