#!/usr/bin/env python3

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.core.logger import log
from src.core.config import AUTH_PROVIDER
from src.crs.crs_service import crs_verify_token, crs_add_account
from src.cpa.cpa_service import cpa_verify_connection
from src.s2a.s2a_service import s2a_verify_connection, s2a_create_account_from_oauth
from src.automation.browser_automation import browser_context, register_and_authorize


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="批量入库账号到授权服务 (支持 CRS/CPA/S2A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从命令行传入账号
  python src/single/ingest_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'

  # 从文件读取账号
  python src/single/ingest_accounts.py --file accounts.json

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


def verify_auth_service() -> Tuple[bool, str]:
    log.step(f"验证授权服务连接 ({AUTH_PROVIDER.upper()})...")

    if AUTH_PROVIDER == "s2a":
        return s2a_verify_connection()
    if AUTH_PROVIDER == "cpa":
        return cpa_verify_connection()
    if AUTH_PROVIDER == "crs":
        return crs_verify_token()

    return False, f"不支持的授权服务: {AUTH_PROVIDER}"


def ingest_single_account(account_info: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    email = account_info["account"]
    password = account_info["password"]

    log.separator()
    log.info(f"处理账号: {email}")
    log.separator()

    with browser_context() as page:
        success, codex_data = register_and_authorize(email, password)
        if success == "domain_blacklisted":
            log.error(f"域名被封禁: {email}")
            return False, "domain_blacklisted"
        if not success:
            log.error(f"授权失败: {email}")
            return False, "authorize_failed"

        if AUTH_PROVIDER == "s2a":
            if (
                not codex_data
                or "code" not in codex_data
                or "session_id" not in codex_data
            ):
                log.error(f"授权数据不完整: {email}")
                return False, "invalid_oauth_data"

            log.step("创建 S2A 账号...")
            s2a_result = s2a_create_account_from_oauth(
                code=codex_data["code"],
                session_id=codex_data["session_id"],
                name=email,
            )
            if not s2a_result:
                log.error(f"S2A 账号创建失败: {email}")
                return False, "s2a_create_failed"

            log.success(f"✅ 账号入库成功: {email} (S2A ID: {s2a_result.get('id')})")
            return True, None

        if AUTH_PROVIDER == "crs":
            if not codex_data:
                log.error(f"授权数据为空: {email}")
                return False, "missing_codex_data"
            crs_result = crs_add_account(email, codex_data)
            if not crs_result:
                log.error(f"CRS 账号入库失败: {email}")
                return False, "crs_add_failed"
            log.success(f"✅ 账号入库成功: {email} (CRS ID: {crs_result.get('id')})")
            return True, None

        log.success(f"✅ 账号入库成功: {email}")
        return True, None


def print_summary(total: int, success_count: int, failed_accounts: List[str]) -> None:
    log.header("处理完成")
    log.info(f"总计: {total} 个账号")
    log.success(f"成功: {success_count} 个")
    if failed_accounts:
        log.error(f"失败: {len(failed_accounts)} 个")
        log.error(f"失败账号: {', '.join(failed_accounts)}")


def main() -> int:
    log.header("账号入库脚本")
    log.info(f"授权服务: {AUTH_PROVIDER.upper()}")

    args = parse_arguments()

    is_valid, message = verify_auth_service()
    if not is_valid:
        log.error(f"{AUTH_PROVIDER.upper()} 服务连接失败: {message}")
        log.error("请检查 config.toml 中的配置")
        return 1

    log.success(f"{AUTH_PROVIDER.upper()} 服务连接成功: {message}")

    accounts = load_accounts(args)
    if not accounts:
        log.error("没有可处理的账号")
        return 1

    total = len(accounts)
    success_count = 0
    failed_accounts: List[str] = []

    for idx, account_info in enumerate(accounts, 1):
        log.info(f"\n进度: {idx}/{total}")
        try:
            success, _ = ingest_single_account(account_info)
            if success:
                success_count += 1
            else:
                failed_accounts.append(account_info["account"])
        except Exception as e:
            log.error(f"处理账号时发生异常: {e}")
            failed_accounts.append(account_info["account"])

        if idx < total:
            time.sleep(2)

    print_summary(total, success_count, failed_accounts)

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
