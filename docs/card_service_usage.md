# 信用卡服务模块使用文档

## 功能概述

信用卡服务模块 (`src/card`) 提供通过卡密 (key_id) 查询信用卡详细信息的功能。

### 主要功能

- 通过卡密查询信用卡完整信息
- 获取卡号、CVV、过期日期
- 获取账单地址信息
- 支持与其他模块集成使用

## 快速开始

### 基本使用

```python
from src.card import query_card_info

# 查询信用卡信息
card_info = query_card_info("your-key-id-here")

if card_info and card_info.is_valid():
    print(f"卡号: {card_info.get_full_card_number()}")
    print(f"CVV: {card_info.get_cvv()}")
    print(f"过期: {card_info.get_expiry()}")
else:
    print("查询失败")
```

## API 参考

### 核心函数

#### `query_card_info(key_id: str) -> Optional[CardInfo]`

通过卡密查询信用卡信息。

**参数:**
- `key_id` (str): 卡密

**返回:**
- `CardInfo` 对象，查询失败返回 `None`

**示例:**
```python
card_info = query_card_info("17859d1b-feaf-45b7-8321-c625aa8b0dcb")
```

## 数据模型

### CardInfo

完整的信用卡信息响应对象。

**属性:**
- `success` (bool): 查询是否成功
- `card` (CardDetails): 信用卡详细信息
- `legal_address` (LegalAddress): 账单地址
- `card_limit` (float): 卡片限额
- `expire_minutes` (int): 剩余有效分钟数
- `used_time` (str): 使用时间

**方法:**

*卡片信息相关:*
- `is_valid() -> bool`: 检查卡片信息是否有效
- `get_full_card_number() -> Optional[str]`: 获取完整卡号
- `get_cvv() -> Optional[str]`: 获取 CVV
- `get_expiry() -> Optional[tuple[str, str]]`: 获取过期日期 (月, 年)

*地址信息相关:*
- `get_billing_address() -> Optional[LegalAddress]`: 获取完整账单地址对象
- `get_address_line1() -> Optional[str]`: 获取地址行1
- `get_address_line2() -> Optional[str]`: 获取地址行2
- `get_city() -> Optional[str]`: 获取城市
- `get_region() -> Optional[str]`: 获取州/地区
- `get_postal_code() -> Optional[str]`: 获取邮编
- `get_country() -> Optional[str]`: 获取国家代码

### CardDetails

信用卡详细信息。

**属性:**
- `account_user_id` (str): 账户用户ID
- `card_id` (str): 卡片ID
- `card_limit` (float): 卡片限额
- `card_type` (str): 卡片类型 (如 "debit")
- `cvv` (str): CVV 安全码
- `exp_month` (str): 过期月份
- `exp_year` (str): 过期年份
- `expire_time` (str): 过期时间
- `pan` (str): 卡号 (Primary Account Number)

### LegalAddress

账单地址信息。

**属性:**
- `address1` (str): 地址行1
- `address2` (str): 地址行2
- `city` (str): 城市
- `country` (str): 国家代码
- `postal_code` (str): 邮编
- `region` (str): 州/地区

## 使用示例

### 示例 1: 基本使用

```python
from src.card import query_card_info

# 查询信用卡信息
card_info = query_card_info("your-key-id-here")

if card_info and card_info.is_valid():
    # 获取卡片信息
    print(f"卡号: {card_info.get_full_card_number()}")
    print(f"CVV: {card_info.get_cvv()}")

    # 获取过期日期
    exp_month, exp_year = card_info.get_expiry()
    print(f"过期日期: {exp_month}/{exp_year}")
```

### 示例 2: 使用细化地址方法（推荐）

```python
from src.card import query_card_info

card_info = query_card_info("your-key-id-here")

if card_info and card_info.is_valid():
    # 直接获取单独的地址字段
    address_line1 = card_info.get_address_line1()
    city = card_info.get_city()
    region = card_info.get_region()
    postal_code = card_info.get_postal_code()
    country = card_info.get_country()

    # 使用这些字段进行后续操作
    print(f"地址: {address_line1}, {city}, {region} {postal_code}, {country}")
```

### 示例 3: 与其他模块集成

```python
from src.card import query_card_info

def process_payment(key_id: str):
    """处理支付流程"""
    # 获取信用卡信息
    card_info = query_card_info(key_id)

    if not card_info or not card_info.is_valid():
        return {"error": "无效的卡密"}

    # 构建支付数据
    payment_data = {
        "card_number": card_info.get_full_card_number(),
        "cvv": card_info.get_cvv(),
        "exp_month": card_info.get_expiry()[0],
        "exp_year": card_info.get_expiry()[1],
        "billing_address": {
            "line1": card_info.get_address_line1(),
            "line2": card_info.get_address_line2(),
            "city": card_info.get_city(),
            "state": card_info.get_region(),
            "zip": card_info.get_postal_code(),
            "country": card_info.get_country(),
        }
    }

    return payment_data
```
