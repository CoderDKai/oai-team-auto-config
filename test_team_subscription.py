#!/usr/bin/env python3
"""查询 Team 订阅信息 (包括注册时间和到期时间)"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import TEAMS
from src.team.team_service import build_invite_headers, http_session, REQUEST_TIMEOUT
from src.core.logger import log
import json


def get_team_subscription_info(team: dict) -> dict:
    """获取 Team 的完整订阅信息"""
    headers = build_invite_headers(team)

    subs_url = (
        f"https://chatgpt.com/backend-api/subscriptions?account_id={team['account_id']}"
    )

    try:
        response = http_session.get(subs_url, headers=headers, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            return response.json()
        else:
            log.error(f"获取订阅信息失败: HTTP {response.status_code}")
            return {}

    except Exception as e:
        log.error(f"获取订阅信息异常: {e}")
        return {}


def main():
    print("\n" + "=" * 60)
    print("Team 订阅信息查询")
    print("=" * 60)

    if not TEAMS:
        print("\n❌ 未找到 Team 配置")
        return

    print(f"\n找到 {len(TEAMS)} 个 Team\n")

    for i, team in enumerate(TEAMS):
        print(f"\n{'=' * 60}")
        print(f"Team {i + 1}: {team['name']}")
        print(f"Owner: {team['owner_email']}")
        print("=" * 60)

        if not team.get("account_id"):
            print("⚠️  未找到 account_id，跳过")
            continue

        print("\n正在获取订阅信息...")
        sub_info = get_team_subscription_info(team)

        if sub_info:
            print("\n✅ 订阅信息:")
            print(json.dumps(sub_info, indent=2, ensure_ascii=False))
        else:
            print("\n❌ 获取失败")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
