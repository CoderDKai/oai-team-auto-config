#!/usr/bin/env python3

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.core.logger import log
from src.core.config import AUTH_PROVIDER
from src.crs.crs_service import crs_verify_token
from src.cpa.cpa_service import cpa_verify_connection
from src.s2a.s2a_service import s2a_verify_connection, s2a_create_account_from_oauth
from src.automation.browser_automation import (
    browser_context,
    register_and_authorize,
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="批量添加账号到授权服务 (支持 CRS/CPA/S2A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从命令行传入账号
  python src/single/batch_add_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
  
  # 从文件读取账号
  python src/single/batch_add_accounts.py --file accounts.json
  
  # accounts.json 格式:
  [
    {"account": "user1@example.com", "password": "password1"},
    {"account": "user2@example.com", "password": "password2"}
  ]
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--accounts",
        type=str,
        help="JSON格式的账号列表字符串",
    )
    group.add_argument(
        "--file",
        type=str,
        help="包含账号列表的JSON文件路径",
    )

    return parser.parse_args()


def load_accounts(args) -> List[Dict[str, str]]:
    try:
        if args.accounts:
            accounts = json.loads(args.accounts)
        else:
            file_path = Path(args.file)
            if not file_path.exists():
                log.error(f"文件不存在: {file_path}")
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                accounts = json.load(f)

        if not isinstance(accounts, list):
            log.error("账号数据必须是列表格式")
            return []

        for acc in accounts:
            if not isinstance(acc, dict):
                log.error(f"账号数据格式错误: {acc}")
                return []
            if "account" not in acc or "password" not in acc:
                log.error(f"账号数据缺少必需字段 (account/password): {acc}")
                return []

        log.success(f"成功加载 {len(accounts)} 个账号")
        return accounts

    except json.JSONDecodeError as e:
        log.error(f"JSON解析失败: {e}")
        return []
    except Exception as e:
        log.error(f"加载账号失败: {e}")
        return []


def verify_auth_service() -> bool:
    log.step(f"验证授权服务连接 ({AUTH_PROVIDER.upper()})...")

    if AUTH_PROVIDER == "s2a":
        is_valid, message = s2a_verify_connection()
    elif AUTH_PROVIDER == "cpa":
        is_valid, message = cpa_verify_connection()
    elif AUTH_PROVIDER == "crs":
        is_valid, message = crs_verify_token()
    else:
        log.error(f"不支持的授权服务: {AUTH_PROVIDER}")
        return False

    if not is_valid:
        log.error(f"{AUTH_PROVIDER.upper()} 服务连接失败: {message}")
        log.error("请检查 config.toml 中的配置")
        return False

    log.success(f"{AUTH_PROVIDER.upper()} 服务连接成功: {message}")
    return True


def process_single_account(account_info: Dict[str, str]) -> bool:
    email = account_info["account"]
    password = account_info["password"]

    log.info(f"\n{'=' * 60}")
    log.info(f"处理账号: {email}")
    log.info(f"{'=' * 60}\n")

    with browser_context() as page:
        success, codex_data = register_and_authorize(email, password)

        if not success:
            log.error(f"注册/授权失败: {email}")
            return False

        if success == "domain_blacklisted":
            log.error(f"域名被封禁: {email}")
            return False

        if AUTH_PROVIDER == "s2a":
            if (
                not codex_data
                or "code" not in codex_data
                or "session_id" not in codex_data
            ):
                log.error(f"授权数据不完整: {email}")
                return False

            log.step("创建 S2A 账号...")
            s2a_result = s2a_create_account_from_oauth(
                code=codex_data["code"],
                session_id=codex_data["session_id"],
                name=email,
            )

            if not s2a_result:
                log.error(f"S2A 账号创建失败: {email}")
                return False

            log.success(f"✅ 账号添加成功: {email} (S2A ID: {s2a_result.get('id')})")
            return True

        log.success(f"✅ 账号添加成功: {email}")
        return True

        # CRS/CPA 模式：授权成功即完成
        log.success(f"✅ 账号添加成功: {email}")
        return True


def main():
    log.info("\n" + "=" * 60)
    log.info("批量账号添加工具")
    log.info(f"授权服务: {AUTH_PROVIDER.upper()}")
    log.info("=" * 60 + "\n")

    args = parse_arguments()

    if not verify_auth_service():
        return 1

    accounts = load_accounts(args)
    if not accounts:
        log.error("没有可处理的账号")
        return 1

    total = len(accounts)
    success_count = 0
    failed_accounts = []

    for idx, account_info in enumerate(accounts, 1):
        log.info(f"\n进度: {idx}/{total}")

        try:
            if process_single_account(account_info):
                success_count += 1
            else:
                failed_accounts.append(account_info["account"])
        except Exception as e:
            log.error(f"处理账号时发生异常: {e}")
            failed_accounts.append(account_info["account"])

        if idx < total:
            time.sleep(2)

    log.info("\n" + "=" * 60)
    log.info("处理完成")
    log.info("=" * 60)
    log.info(f"总计: {total} 个账号")
    log.success(f"成功: {success_count} 个")
    if failed_accounts:
        log.error(f"失败: {len(failed_accounts)} 个")
        log.error(f"失败账号: {', '.join(failed_accounts)}")
    log.info("=" * 60 + "\n")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log.warning("\n用户中断")
        sys.exit(1)
    except Exception as e:
        log.error(f"程序异常: {e}")
        sys.exit(1)
