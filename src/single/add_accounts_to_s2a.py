#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的S2A账号添加脚本

功能:
1. 从JSON输入读取账号列表 [{"account": "email", "password": "pwd"}]
2. 逐个将账号添加到S2A中
3. 若遇到验证码，在命令行等待用户手动输入
4. 若用户未注册，执行注册流程（填写用户信息）
5. 然后继续执行添加到S2A流程

使用方法:
    python src/single/add_accounts_to_s2a.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
    或
    python src/single/add_accounts_to_s2a.py --file accounts.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到路径
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.core.logger import log
from src.core.config import (
    S2A_API_BASE,
    S2A_ADMIN_KEY,
    S2A_ADMIN_TOKEN,
)
from src.s2a.s2a_service import (
    s2a_verify_connection,
    s2a_generate_auth_url,
    s2a_create_account_from_oauth,
    s2a_check_account_exists,
    extract_code_from_url,
    is_s2a_callback_url,
)
from src.automation.browser_automation import (
    browser_context,
    wait_for_page_stable,
    wait_for_element,
    wait_for_url_change,
    type_slowly,
    human_delay,
    log_current_url,
    log_url_change,
    is_logged_in,
    check_and_handle_error,
)
from src.core.config import get_random_name, get_random_birthday


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="批量添加账号到S2A",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从命令行传入账号
  python src/single/add_accounts_to_s2a.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
  
  # 从文件读取账号
  python src/single/add_accounts_to_s2a.py --file accounts.json
  
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
    """加载账号列表"""
    try:
        if args.accounts:
            # 从命令行参数加载
            accounts = json.loads(args.accounts)
        else:
            # 从文件加载
            file_path = Path(args.file)
            if not file_path.exists():
                log.error(f"文件不存在: {file_path}")
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                accounts = json.load(f)

        # 验证格式
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


def register_or_login_account(page, email: str, password: str) -> bool:
    """注册或登录账号

    Args:
        page: 浏览器页面实例
        email: 邮箱地址
        password: 密码

    Returns:
        bool: 是否成功
    """
    log.info(f"开始注册/登录账号: {email}", icon="account")

    try:
        # 打开ChatGPT首页
        url = "https://chatgpt.com"
        log.step(f"打开 {url}")
        page.get(url)

        # 等待页面加载
        wait_for_page_stable(page, timeout=8)
        log_current_url(page, "页面加载完成", force=True)

        # 检查是否已登录
        try:
            if is_logged_in(page):
                log.success("检测到已登录，跳过注册步骤")
                return True
        except Exception:
            pass

        # 点击注册/登录按钮
        log.step("点击注册/登录按钮...")
        signup_btn = wait_for_element(
            page, 'css:[data-testid="signup-button"]', timeout=5
        )
        if not signup_btn:
            signup_btn = wait_for_element(page, "text:免费注册", timeout=3)
        if not signup_btn:
            signup_btn = wait_for_element(page, "text:Sign up", timeout=3)
        if not signup_btn:
            signup_btn = wait_for_element(page, "text:登录", timeout=3)

        if signup_btn:
            old_url = page.url
            signup_btn.click()
            time.sleep(2)
            if page.url != old_url:
                log_url_change(page, old_url, "点击注册按钮")

        # 输入邮箱
        log.step("输入邮箱...")
        email_input = wait_for_element(page, 'css:input[type="email"]', timeout=15)
        if not email_input:
            log.error("无法找到邮箱输入框")
            return False

        human_delay()
        type_slowly(page, 'css:input[type="email"]', email)
        log.success("邮箱已输入")

        # 点击继续
        human_delay(0.5, 1.2)
        log.step("点击继续...")
        continue_btn = wait_for_element(page, 'css:button[type="submit"]', timeout=5)
        if continue_btn:
            old_url = page.url
            continue_btn.click()
            wait_for_url_change(page, old_url, timeout=10)

        current_url = page.url
        log_current_url(page, "邮箱输入后")

        # 处理密码页面
        if "/password" in current_url:
            log.step("输入密码...")
            password_input = wait_for_element(
                page, 'css:input[type="password"]', timeout=10
            )
            if not password_input:
                log.error("无法找到密码输入框")
                return False

            human_delay()
            type_slowly(page, 'css:input[type="password"]', password)
            log.success("密码已输入")

            # 点击继续
            human_delay(0.5, 1.2)
            log.step("点击继续...")
            continue_btn = wait_for_element(
                page, 'css:button[type="submit"]', timeout=5
            )
            if continue_btn:
                old_url = page.url
                continue_btn.click()
                time.sleep(2)

                # 检查是否密码错误
                try:
                    error_text = page.ele(
                        "text:Incorrect email address or password", timeout=1
                    )
                    if error_text and error_text.states.is_displayed:
                        log.warning("密码错误，尝试使用一次性验证码登录...")
                        otp_btn = wait_for_element(
                            page, "text=使用一次性验证码登录", timeout=3
                        )
                        if not otp_btn:
                            otp_btn = wait_for_element(
                                page, "text=Log in with a one-time code", timeout=3
                            )
                        if otp_btn:
                            otp_btn.click()
                            wait_for_url_change(page, old_url, timeout=10)
                except Exception:
                    pass

        current_url = page.url

        # 处理验证码页面
        if "email-verification" in current_url or page.ele(
            'css:input[name="code"]', timeout=2
        ):
            log_current_url(page, "邮箱验证码页面")
            log.warning(f"检测到验证码页面，请查收邮箱: {email}")

            verification_code = input("⚠️ 请在终端输入验证码: ").strip()

            if not verification_code:
                log.error("未输入验证码")
                return False

            # 输入验证码
            log.step(f"输入验证码: {verification_code}")
            code_input = wait_for_element(page, 'css:input[name="code"]', timeout=10)
            if not code_input:
                code_input = wait_for_element(
                    page, 'css:input[placeholder*="代码"]', timeout=5
                )

            if code_input:
                try:
                    code_input.clear()
                except Exception:
                    pass
                type_slowly(
                    page,
                    'css:input[name="code"], input[placeholder*="代码"]',
                    verification_code,
                    base_delay=0.08,
                )
                time.sleep(0.5)

                # 点击继续
                log.step("点击继续...")
                continue_btn = wait_for_element(
                    page, 'css:button[type="submit"]', timeout=10
                )
                if continue_btn:
                    continue_btn.click()
                    time.sleep(2)

        # 处理个人信息页面
        current_url = page.url
        if "about-you" in current_url or page.ele('css:input[name="name"]', timeout=2):
            log_current_url(page, "个人信息页面")
            log.info("填写个人信息...")

            # 输入姓名
            random_name = get_random_name()
            log.step(f"输入姓名: {random_name}")
            name_input = wait_for_element(page, 'css:input[name="name"]', timeout=10)
            if not name_input:
                name_input = wait_for_element(
                    page, 'css:input[autocomplete="name"]', timeout=5
                )

            if name_input:
                type_slowly(
                    page,
                    'css:input[name="name"], input[autocomplete="name"]',
                    random_name,
                )

            # 输入生日
            birthday = get_random_birthday()
            log.step(
                f"输入生日: {birthday['year']}/{birthday['month']}/{birthday['day']}"
            )

            # 年份
            year_input = wait_for_element(page, 'css:[data-type="year"]', timeout=10)
            if year_input:
                year_input.click()
                time.sleep(0.15)
                year_input.input(birthday["year"], clear=True)
                time.sleep(0.2)

            # 月份
            month_input = wait_for_element(page, 'css:[data-type="month"]', timeout=5)
            if month_input:
                month_input.click()
                time.sleep(0.15)
                month_input.input(birthday["month"], clear=True)
                time.sleep(0.2)

            # 日期
            day_input = wait_for_element(page, 'css:[data-type="day"]', timeout=5)
            if day_input:
                day_input.click()
                time.sleep(0.15)
                day_input.input(birthday["day"], clear=True)

            log.success("生日已输入")

            # 点击提交
            log.step("点击提交...")
            time.sleep(0.5)
            submit_btn = wait_for_element(page, 'css:button[type="submit"]', timeout=5)
            if submit_btn:
                submit_btn.click()
                time.sleep(2)

        # 检查是否登录成功
        try:
            if is_logged_in(page):
                log.success(f"账号注册/登录成功: {email}")
                return True
        except Exception:
            pass

        log.error("注册/登录流程未完成")
        return False

    except Exception as e:
        log.error(f"注册/登录失败: {e}")
        return False


def perform_s2a_authorization(page, email: str, password: str) -> Optional[Dict]:
    """执行S2A授权流程

    Args:
        page: 浏览器页面实例
        email: 邮箱地址
        password: 密码

    Returns:
        dict: 账号数据 或 None
    """
    log.info(f"开始S2A授权: {email}", icon="code")

    # 生成授权URL
    auth_url, session_id = s2a_generate_auth_url()
    if not auth_url or not session_id:
        log.error("无法获取S2A授权URL")
        return None

    # 打开授权页面
    log.step("打开S2A授权页面...")
    log.info(f"[URL] 授权URL: {auth_url}", icon="browser")
    page.get(auth_url)
    wait_for_page_stable(page, timeout=5)
    log_current_url(page, "S2A授权页面加载完成", force=True)

    try:
        # 输入邮箱
        log.step("输入邮箱...")
        email_input = wait_for_element(page, 'css:input[type="email"]', timeout=10)
        if not email_input:
            email_input = wait_for_element(page, 'css:input[name="email"]', timeout=5)

        if email_input:
            type_slowly(
                page,
                'css:input[type="email"], input[name="email"]',
                email,
                base_delay=0.06,
            )

            # 点击继续
            log.step("点击继续...")
            continue_btn = wait_for_element(
                page, 'css:button[type="submit"]', timeout=5
            )
            if continue_btn:
                old_url = page.url
                continue_btn.click()
                wait_for_url_change(page, old_url, timeout=8)
                log_url_change(page, old_url, "输入邮箱后")

    except Exception as e:
        log.warning(f"邮箱输入步骤异常: {e}")

    current_url = page.url
    log_current_url(page, "邮箱步骤完成后")

    # 处理密码页面
    if "/password" in current_url:
        try:
            log.step("输入密码...")
            password_input = wait_for_element(
                page, 'css:input[type="password"]', timeout=10
            )
            if password_input:
                type_slowly(
                    page, 'css:input[type="password"]', password, base_delay=0.06
                )

                # 点击继续
                log.step("点击继续...")
                continue_btn = wait_for_element(
                    page, 'css:button[type="submit"]', timeout=5
                )
                if continue_btn:
                    old_url = page.url
                    continue_btn.click()
                    wait_for_url_change(page, old_url, timeout=8)
                    log_url_change(page, old_url, "输入密码后")

        except Exception as e:
            log.warning(f"密码输入步骤异常: {e}")

    # 等待授权回调
    max_wait = 45
    start_time = time.time()
    code = None
    log.step(f"等待授权回调 (最多 {max_wait}s)...")

    while time.time() - start_time < max_wait:
        try:
            current_url = page.url

            # 检查是否到达回调页面
            if is_s2a_callback_url(current_url):
                log.success("获取到S2A回调URL")
                log.info(f"[URL] 回调地址: {current_url}", icon="browser")
                code = extract_code_from_url(current_url)
                if code:
                    log.success("提取授权码成功")
                    break

            # 尝试点击授权按钮
            try:
                buttons = page.eles('css:button[type="submit"]')
                for btn in buttons:
                    if btn.states.is_displayed and btn.states.is_enabled:
                        btn_text = btn.text.lower()
                        if any(
                            x in btn_text
                            for x in [
                                "allow",
                                "authorize",
                                "continue",
                                "授权",
                                "允许",
                                "继续",
                                "accept",
                            ]
                        ):
                            log.step(f"点击按钮: {btn.text}")
                            btn.click()
                            time.sleep(1.5)
                            break
            except Exception:
                pass

            elapsed = int(time.time() - start_time)
            log.progress_inline(f"[等待中... {elapsed}s]")
            time.sleep(1.5)

        except Exception as e:
            log.warning(f"检查异常: {e}")
            time.sleep(1.5)

    if not code:
        log.warning("授权超时")
        try:
            current_url = page.url
            if "code=" in current_url:
                code = extract_code_from_url(current_url)
        except Exception:
            pass

    if not code:
        log.error("无法获取授权码")
        return None

    # 创建S2A账号
    log.step("创建S2A账号...")
    account_data = s2a_create_account_from_oauth(code, session_id, name=email)

    if account_data:
        log.success(f"S2A账号创建成功: {email}")
        return account_data
    else:
        log.error("S2A账号创建失败")
        return None


def process_single_account(account_info: Dict[str, str]) -> bool:
    """处理单个账号

    Args:
        account_info: 账号信息 {"account": "email", "password": "pwd"}

    Returns:
        bool: 是否成功
    """
    email = account_info["account"]
    password = account_info["password"]

    log.info(f"\n{'=' * 60}")
    log.info(f"处理账号: {email}")
    log.info(f"{'=' * 60}\n")

    # 检查账号是否已存在
    if s2a_check_account_exists(email):
        log.warning(f"账号已存在于S2A中: {email}")
        return True

    # 使用浏览器自动化
    with browser_context() as page:
        # 步骤1: 注册或登录账号
        if not register_or_login_account(page, email, password):
            log.error(f"账号注册/登录失败: {email}")
            return False

        # 步骤2: 执行S2A授权
        account_data = perform_s2a_authorization(page, email, password)
        if not account_data:
            log.error(f"S2A授权失败: {email}")
            return False

        log.success(f"✅ 账号添加成功: {email}")
        return True


def main():
    """主函数"""
    # 打印标题
    log.info("\n" + "=" * 60)
    log.info("S2A 账号批量添加工具")
    log.info("=" * 60 + "\n")

    # 解析参数
    args = parse_arguments()

    # 验证S2A连接
    log.step("验证S2A服务连接...")
    is_valid, message = s2a_verify_connection()
    if not is_valid:
        log.error(f"S2A服务连接失败: {message}")
        log.error("请检查config.toml中的S2A配置")
        return 1
    log.success(f"S2A服务连接成功: {message}")

    # 加载账号列表
    accounts = load_accounts(args)
    if not accounts:
        log.error("没有可处理的账号")
        return 1

    # 统计信息
    total = len(accounts)
    success_count = 0
    failed_accounts = []

    # 逐个处理账号
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

        # 账号之间稍作延迟
        if idx < total:
            time.sleep(2)

    # 打印总结
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
