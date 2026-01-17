#!/usr/bin/env python3
"""Domain Mail 服务集成测试脚本"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import (
    EMAIL_PROVIDER,
    DOMAINMAIL_API_BASE,
    DOMAINMAIL_API_KEY,
    DOMAINMAIL_DOMAINS,
)
from src.email.email_service import domainmail_service


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("Domain Mail 配置测试")
    print("=" * 60)
    print(f"当前邮箱提供商: {EMAIL_PROVIDER}")
    print(f"API Base: {DOMAINMAIL_API_BASE}")
    print(f"API Key: {DOMAINMAIL_API_KEY[:20]}..." if DOMAINMAIL_API_KEY else "未配置")
    print(f"可用域名数量: {len(DOMAINMAIL_DOMAINS)}")
    if DOMAINMAIL_DOMAINS:
        print(f"域名列表: {', '.join(DOMAINMAIL_DOMAINS[:3])}...")
    print()


def test_service_init():
    """测试服务初始化"""
    print("=" * 60)
    print("Domain Mail 服务初始化测试")
    print("=" * 60)
    print(f"服务实例: {domainmail_service}")
    print(f"API Base: {domainmail_service.api_base}")
    print(f"API Key 已配置: {'是' if domainmail_service.api_key else '否'}")
    print()


def main():
    """主测试函数"""
    print("\n🚀 Domain Mail 服务集成测试\n")

    test_config()
    test_service_init()

    print("=" * 60)
    print("✅ 集成测试完成")
    print("=" * 60)
    print("\n提示:")
    print("1. 请在 config.toml 中配置 Domain Mail 相关参数")
    print("2. 设置 email_provider = 'domainmail'")
    print("3. 配置 api_base, api_key 和 domains")
    print()


if __name__ == "__main__":
    main()
