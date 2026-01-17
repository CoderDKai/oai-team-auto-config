#!/usr/bin/env python3
"""Domain Mail API 连接测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.email.email_service import domainmail_service
from src.core.logger import log


def test_api_connection():
    """测试 API 连接"""
    print("\n" + "=" * 60)
    print("Domain Mail API 连接测试")
    print("=" * 60)

    test_email = "test123oaiteam@410883.xyz"

    print(f"\n1. 测试创建邮箱: {test_email}")
    mailbox, error = domainmail_service.create_mailbox(test_email)

    if mailbox:
        print(f"   ✅ 邮箱创建成功!")
        print(f"   邮箱 ID: {mailbox.get('id', 'N/A')}")
        print(f"   地址: {mailbox.get('address', 'N/A')}")
        print(f"   状态: {'启用' if mailbox.get('enabled') else '禁用'}")
    elif error and "already exists" in str(error).lower():
        print(f"   ℹ️  邮箱已存在 (这是正常的)")
    else:
        print(f"   ❌ 邮箱创建失败: {error}")
        return False

    print(f"\n2. 测试获取邮件列表")
    emails, error = domainmail_service.get_emails(test_email, page=1, limit=5)

    if error:
        print(f"   ❌ 获取邮件失败: {error}")
        return False
    else:
        print(f"   ✅ 获取邮件成功!")
        print(f"   邮件数量: {len(emails)}")
        if emails:
            print(f"   最新邮件: {emails[0].get('subject', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ API 连接测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_api_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        log.error(f"测试异常: {e}")
        sys.exit(1)
