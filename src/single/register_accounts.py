#!/usr/bin/env python3

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.core.logger import log
from src.automation.browser_automation import browser_context, register_openai_account


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="批量注册 OpenAI 账号",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从命令行传入账号
  python src/single/register_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'

  # 从文件读取账号
  python src/single/register_accounts.py --file accounts.json

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


def register_single_account(account_info: Dict[str, str]) -> bool:
    email = account_info["account"]
    password = account_info["password"]

    log.info(f"\n{'=' * 60}")
    log.info(f"处理账号: {email}")
    log.info(f"{'=' * 60}\n")

    with browser_context() as page:
        result = register_openai_account(page, email, password)
        if result == "domain_blacklisted":
            log.error(f"域名被封禁: {email}")
            return False
        if not result:
            log.error(f"注册失败: {email}")
            return False

    log.success(f"✅ 注册成功: {email}")
    return True


def main() -> int:
    log.info("\n" + "=" * 60)
    log.info("账号注册脚本")
    log.info("=" * 60 + "\n")

    args = parse_arguments()
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
            if register_single_account(account_info):
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
