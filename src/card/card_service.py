# ==================== Card 服务模块 ====================
# 处理信用卡信息查询功能
#
# 功能说明:
# - 支持多个信用卡服务商 (holy, niko)
# - 通过卡密 (key_id) 查询信用卡详细信息
# - 返回卡号、CVV、过期日期、账单地址等完整信息
# - 支持与其他模块集成使用

from dataclasses import dataclass
from typing import Optional

from src.core.logger import log
from .providers import HolyProvider, NikoProvider


# ==================== 数据模型 ====================

@dataclass
class CardDetails:
    """信用卡详细信息"""
    account_user_id: str
    card_id: str
    card_limit: float
    card_type: str
    cvv: str
    exp_month: str
    exp_year: str
    expire_time: str
    pan: str  # Primary Account Number (卡号)

    def __str__(self):
        """格式化输出卡片信息（隐藏敏感信息）"""
        masked_pan = f"{self.pan[:4]}****{self.pan[-4:]}" if len(self.pan) >= 8 else "****"
        return (
            f"卡号: {masked_pan} | "
            f"类型: {self.card_type} | "
            f"过期: {self.exp_month}/{self.exp_year} | "
            f"限额: ${self.card_limit}"
        )


@dataclass
class LegalAddress:
    """账单地址信息"""
    address1: str
    address2: str
    city: str
    country: str
    postal_code: str
    region: str

    def __str__(self):
        """格式化输出地址"""
        addr_parts = [self.address1]
        if self.address2:
            addr_parts.append(self.address2)
        addr_parts.extend([self.city, self.region, self.postal_code, self.country])
        return ", ".join(addr_parts)


@dataclass
class CardInfo:
    """完整的信用卡信息响应"""
    success: bool
    card: Optional[CardDetails]
    legal_address: Optional[LegalAddress]
    card_limit: float
    expire_minutes: int
    used_time: str

    def is_valid(self) -> bool:
        """检查卡片信息是否有效"""
        return self.success and self.card is not None

    def get_full_card_number(self) -> Optional[str]:
        """获取完整卡号"""
        return self.card.pan if self.card else None

    def get_cvv(self) -> Optional[str]:
        """获取 CVV"""
        return self.card.cvv if self.card else None

    def get_expiry(self) -> Optional[tuple[str, str]]:
        """获取过期日期 (月, 年)"""
        if self.card:
            return (self.card.exp_month, self.card.exp_year)
        return None

    def get_billing_address(self) -> Optional[LegalAddress]:
        """获取完整账单地址对象"""
        return self.legal_address

    def get_address_line1(self) -> Optional[str]:
        """获取地址行1"""
        return self.legal_address.address1 if self.legal_address else None

    def get_address_line2(self) -> Optional[str]:
        """获取地址行2"""
        return self.legal_address.address2 if self.legal_address else None

    def get_city(self) -> Optional[str]:
        """获取城市"""
        return self.legal_address.city if self.legal_address else None

    def get_region(self) -> Optional[str]:
        """获取州/地区"""
        return self.legal_address.region if self.legal_address else None

    def get_postal_code(self) -> Optional[str]:
        """获取邮编"""
        return self.legal_address.postal_code if self.legal_address else None

    def get_country(self) -> Optional[str]:
        """获取国家代码"""
        return self.legal_address.country if self.legal_address else None


# ==================== 辅助函数 ====================

def parse_card_response(data: dict) -> Optional[CardInfo]:
    """解析 API 响应数据为 CardInfo 对象

    Args:
        data: API 响应的 JSON 数据

    Returns:
        CardInfo 对象，解析失败返回 None
    """
    try:
        # 解析卡片详细信息
        card_data = data.get("card")
        card_details = None
        if card_data:
            card_details = CardDetails(
                account_user_id=card_data.get("account_user_id", ""),
                card_id=card_data.get("card_id", ""),
                card_limit=card_data.get("card_limit", 0.0),
                card_type=card_data.get("card_type", ""),
                cvv=card_data.get("cvv", ""),
                exp_month=card_data.get("exp_month", ""),
                exp_year=card_data.get("exp_year", ""),
                expire_time=card_data.get("expire_time", ""),
                pan=card_data.get("pan", ""),
            )

        # 解析账单地址
        address_data = data.get("legal_address")
        legal_address = None
        if address_data:
            legal_address = LegalAddress(
                address1=address_data.get("address1", ""),
                address2=address_data.get("address2", ""),
                city=address_data.get("city", ""),
                country=address_data.get("country", ""),
                postal_code=address_data.get("postal_code", ""),
                region=address_data.get("region", ""),
            )

        # 构建完整的 CardInfo 对象
        card_info = CardInfo(
            success=data.get("success", False),
            card=card_details,
            legal_address=legal_address,
            card_limit=data.get("card_limit", 0.0),
            expire_minutes=data.get("expire_minutes", 0),
            used_time=data.get("used_time", ""),
        )

        return card_info

    except Exception as e:
        log.error(f"解析信用卡响应数据失败: {e}")
        return None


# ==================== 服务商管理 ====================

# 服务商实例缓存
_providers = {
    "holy": HolyProvider(),
    "niko": NikoProvider(),
}


def get_provider(provider_name: str):
    """获取服务商实例

    Args:
        provider_name: 服务商名称 ("holy" 或 "niko")

    Returns:
        服务商实例

    Raises:
        ValueError: 不支持的服务商
    """
    provider = _providers.get(provider_name.lower())
    if not provider:
        raise ValueError(f"不支持的服务商: {provider_name}，支持的服务商: {list(_providers.keys())}")
    return provider


# ==================== 统一入口函数 ====================

def query_card_info(key_id: str, provider: str = "holy") -> Optional[CardInfo]:
    """通过卡密查询信用卡信息

    Args:
        key_id: 卡密
        provider: 服务商名称，默认 "holy"，可选 "niko"

    Returns:
        CardInfo 对象，查询失败返回 None

    Example:
        >>> # 使用 holy 服务商
        >>> card_info = query_card_info("your-key-id", provider="holy")
        >>>
        >>> # 使用 niko 服务商
        >>> card_info = query_card_info("your-key-id", provider="niko")
        >>>
        >>> if card_info and card_info.is_valid():
        >>>     print(f"卡号: {card_info.get_full_card_number()}")
        >>>     print(f"CVV: {card_info.get_cvv()}")
    """
    try:
        provider_instance = get_provider(provider)
        data = provider_instance.query_card_info(key_id)

        if data:
            card_info = parse_card_response(data)
            if card_info and card_info.is_valid():
                log.success(f"查询成功: {card_info.card}")
                log.info(f"账单地址: {card_info.legal_address}")
            return card_info

        return None

    except ValueError as e:
        log.error(str(e))
        return None
    except Exception as e:
        log.error(f"查询异常: {e}")
        return None


def redeem_card(key_id: str, provider: str = "niko") -> bool:
    """激活卡密

    Args:
        key_id: 卡密
        provider: 服务商名称，默认 "niko"

    Returns:
        是否激活成功

    Example:
        >>> # 激活 niko 服务商的卡密
        >>> success = redeem_card("your-key-id", provider="niko")
        >>> if success:
        >>>     print("激活成功")
    """
    try:
        provider_instance = get_provider(provider)
        return provider_instance.redeem_card(key_id)

    except ValueError as e:
        log.error(str(e))
        return False
    except Exception as e:
        log.error(f"激活异常: {e}")
        return False
