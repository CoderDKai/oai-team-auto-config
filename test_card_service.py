#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信用卡服务测试脚本 - 多服务商支持
用于测试通过卡密获取信用卡信息的功能
支持 holy 和 niko 两个服务商
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.card import query_card_info, redeem_card


def print_separator(char="=", length=60):
    """打印分隔线"""
    print(char * length)


def print_card_details(card_info, provider_name):
    """打印信用卡详细信息"""
    if not card_info or not card_info.is_valid():
        print(f"\n✗ [{provider_name}] 查询失败！")
        return False

    print(f"\n✓ [{provider_name}] 查询成功！\n")
    print_separator("-")
    print("信用卡详细信息:")
    print_separator("-")
    print(f"卡号 (PAN):        {card_info.get_full_card_number()}")
    print(f"CVV:              {card_info.get_cvv()}")

    expiry = card_info.get_expiry()
    if expiry:
        print(f"过期日期:          {expiry[0]}/{expiry[1]}")

    print(f"卡片类型:          {card_info.card.card_type}")
    print(f"卡片限额:          ${card_info.card_limit}")

    print("\n" + "-" * 60)
    print("账单地址 (使用细化方法):")
    print_separator("-")
    print(f"地址行1:          {card_info.get_address_line1()}")
    if card_info.get_address_line2():
        print(f"地址行2:          {card_info.get_address_line2()}")
    print(f"城市:            {card_info.get_city()}")
    print(f"州/地区:          {card_info.get_region()}")
    print(f"邮编:            {card_info.get_postal_code()}")
    print(f"国家:            {card_info.get_country()}")

    return True


def test_holy_provider():
    """测试 Holy 服务商"""
    print_separator()
    print("测试 Holy 服务商")
    print_separator()

    # Holy 测试卡密
    test_key_id = "17859d1b-feaf-45b7-8321-c625aa8b0dcb"
    print(f"\n测试卡密: {test_key_id}\n")

    # 查询信用卡信息
    card_info = query_card_info(test_key_id, provider="holy")
    return print_card_details(card_info, "Holy")


def test_niko_provider():
    """测试 Niko 服务商"""
    print("\n\n")
    print_separator()
    print("测试 Niko 服务商")
    print_separator()

    # Niko 测试卡密
    test_key_id = "0277ff32-f2f3-40f8-84b7-700211c88c10"
    print(f"\n测试卡密: {test_key_id}\n")

    # 查询信用卡信息
    card_info = query_card_info(test_key_id, provider="niko")
    return print_card_details(card_info, "Niko")


def show_integration_example():
    """展示集成使用示例"""
    print("\n\n")
    print_separator()
    print("集成使用示例")
    print_separator()

    print("\n示例代码:")
    print_separator("-")
    print("""
from src.card import query_card_info, redeem_card

# 方式1: 使用 Holy 服务商（默认）
card_info = query_card_info("your-key-id")

# 方式2: 显式指定 Holy 服务商
card_info = query_card_info("your-key-id", provider="holy")

# 方式3: 使用 Niko 服务商
card_info = query_card_info("your-key-id", provider="niko")

# 获取信用卡信息
if card_info and card_info.is_valid():
    # 获取卡片信息
    card_number = card_info.get_full_card_number()
    cvv = card_info.get_cvv()
    exp_month, exp_year = card_info.get_expiry()

    # 获取地址信息（细化方法）
    address_line1 = card_info.get_address_line1()
    city = card_info.get_city()
    postal_code = card_info.get_postal_code()
    country = card_info.get_country()

    print(f"卡号: {card_number}")
    print(f"CVV: {cvv}")
    print(f"过期: {exp_month}/{exp_year}")
    print(f"地址: {address_line1}, {city}, {postal_code}, {country}")

# Niko 服务商支持激活功能
# success = redeem_card("your-key-id", provider="niko")
""")
    print_separator("-")


if __name__ == "__main__":
    # 运行测试
    holy_success = test_holy_provider()
    niko_success = test_niko_provider()

    # 显示集成示例
    show_integration_example()

    # 总结
    print("\n\n")
    print_separator()
    print("测试总结")
    print_separator()
    print(f"Holy 服务商: {'✓ 通过' if holy_success else '✗ 失败'}")
    print(f"Niko 服务商: {'✓ 通过' if niko_success else '✗ 失败'}")
    print_separator()

    # 退出
    sys.exit(0 if (holy_success and niko_success) else 1)
