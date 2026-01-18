#!/usr/bin/env python3

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.core.logger import log
from src.core.config import get_random_name
from src.automation.browser_automation import (
    browser_context,
    register_openai_account,
    wait_for_element,
    wait_for_page_stable,
    type_slowly,
    human_delay,
    log_current_url,
)
from src.card.card_service import query_card_info, CardInfo


# ==================== 支付信息配置 ====================
PAYMENT_INFO = {
    "card_number": "5342711094650064",
    "expiry": "01/32",
    "cvv": "234",
    "billing_address": "55 South Forest Street, Denver, CO 80246, US",
}


def get_payment_info(card_key_id: Optional[str] = None, card_provider: str = "holy") -> Optional[Dict[str, str]]:
    """获取支付信息

    Args:
        card_key_id: 可选的卡密ID，如果提供则从card服务获取
        card_provider: 卡服务商名称，默认 "holy"，可选 "niko"

    Returns:
        支付信息字典，包含card_number, expiry, cvv, billing_address等
        如果获取失败返回None
    """
    if not card_key_id:
        log.info("使用默认支付信息")
        return PAYMENT_INFO

    log.info(f"从card服务获取支付信息 (provider: {card_provider}, card_key_id: {card_key_id[:8]}...)")
    card_info = query_card_info(card_key_id, provider=card_provider)

    if not card_info or not card_info.is_valid():
        log.error("获取card信息失败，使用默认支付信息")
        return PAYMENT_INFO

    # 格式化过期日期为 MM/YY 格式
    exp_month, exp_year = card_info.get_expiry()
    expiry = f"{exp_month}/{exp_year[-2:]}"  # 只取年份后两位

    # 格式化账单地址
    address = card_info.get_billing_address()
    billing_address = f"{address.address1}, {address.city}, {address.region} {address.postal_code}, {address.country}"

    payment_info = {
        "card_number": card_info.get_full_card_number(),
        "expiry": expiry,
        "cvv": card_info.get_cvv(),
        "billing_address": billing_address,
    }

    log.success(f"成功获取card信息: {card_info.card}")
    return payment_info


def parse_billing_address(address_string: str) -> Dict[str, str]:
    """解析账单地址字符串

    格式: "55 South Forest Street, Denver, CO 80246, US"
    返回: {"street": "55 South Forest Street", "city": "Denver", "state": "CO", "zip": "80246"}
    """
    try:
        parts = [p.strip() for p in address_string.split(",")]
        if len(parts) >= 3:
            street = parts[0]
            city = parts[1]
            state_zip = parts[2].split()
            state = state_zip[0] if len(state_zip) > 0 else ""
            zip_code = state_zip[1] if len(state_zip) > 1 else ""

            return {
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code
            }
    except Exception as e:
        log.error(f"解析地址失败: {e}")

    return {"street": "", "city": "", "state": "", "zip": ""}


def verify_address_filled(page) -> bool:
    """验证地址是否已成功填充

    通过检查 billingLocality 字段是否有内容来判断
    """
    log.step("验证地址是否已填充...")

    locality_input = wait_for_element(
        page, 'css:input[name="billingLocality"]', timeout=5
    )

    if not locality_input:
        log.error("❌ 无法找到 billingLocality 字段，无法验证地址")
        return False

    # 获取字段的值
    try:
        locality_value = locality_input.attr("value") or ""
        if locality_value.strip():
            log.success(f"✅ 地址已成功填充，城市: {locality_value}")
            return True
        else:
            log.error("❌ billingLocality 字段为空，地址填写失败")
            return False
    except Exception as e:
        log.error(f"❌ 获取 billingLocality 值时出错: {e}")
        return False


def manual_fill_address(page) -> bool:
    """手动填写地址表单

    当自动补全失败时，尝试手动填写地址字段
    """
    try:
        log.step("尝试手动填写地址...")

        # 解析地址信息
        address_parts = parse_billing_address(PAYMENT_INFO["billing_address"])
        log.info(f"解析的地址信息: {address_parts}")

        # 1. 尝试点击 "Enter address manually" 按钮
        manual_btn = wait_for_element(
            page, "css:button.Button--checkoutSecondaryLink", timeout=5
        )

        if manual_btn:
            human_delay(0.3, 0.6)
            manual_btn.click()
            log.success("已点击手动输入地址按钮")
            time.sleep(1)

        # 2. 填写地址行1
        log.step("填写地址行1...")
        street_input = wait_for_element(
            page, 'css:input[name="billingAddressLine1"]', timeout=10
        )

        if street_input:
            # 先清空输入框
            try:
                street_input.clear()
                log.info("已清空地址行1输入框")
            except Exception as e:
                log.warning(f"清空地址行1失败: {e}")

            human_delay(0.3, 0.6)
            type_slowly(page, street_input, address_parts["street"])
            log.success(f"地址行1已输入: {address_parts['street']}")
        else:
            log.error("未找到地址行1输入框")
            return False

        # 3. 填写城市
        log.step("填写城市...")
        city_input = wait_for_element(
            page, 'css:input[name="billingLocality"]', timeout=10
        )

        if city_input:
            human_delay(0.3, 0.6)
            type_slowly(page, city_input, address_parts["city"])
            log.success(f"城市已输入: {address_parts['city']}")
        else:
            log.error("未找到城市输入框")
            return False

        # 4. 选择州
        log.step("选择州...")
        state_select = wait_for_element(
            page, 'css:select[name="billingAdministrativeArea"]', timeout=10
        )

        if state_select:
            try:
                human_delay(0.3, 0.6)
                state_select.select_option(value=address_parts["state"])
                log.success(f"州已选择: {address_parts['state']}")
            except Exception as e:
                log.error(f"选择州失败: {e}")
                return False
        else:
            log.error("未找到州选择框")
            return False

        # 5. 填写邮编
        log.step("填写邮编...")
        zip_input = wait_for_element(
            page, 'css:input[name="billingPostalCode"]', timeout=10
        )

        if zip_input:
            human_delay(0.3, 0.6)
            type_slowly(page, zip_input, address_parts["zip"])
            log.success(f"邮编已输入: {address_parts['zip']}")
        else:
            log.error("未找到邮编输入框")
            return False

        log.success("✅ 手动地址填写完成")
        return True

    except Exception as e:
        log.error(f"手动填写地址异常: {e}")
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="批量注册 OpenAI 母号并订阅 Team",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从命令行传入账号
  python src/single/register_parent_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'

  # 从文件读取账号
  python src/single/register_parent_accounts.py --file accounts.json

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


def check_payment_price(page) -> bool:
    """检查支付页面的价格是否为 $0.00

    Returns:
        True: 价格为 $0.00，可以继续
        False: 价格不为 $0.00，需要重试
    """
    log.step("检查支付价格...")

    try:
        # 等待页面加载
        time.sleep(2)

        # 查找第一个 CurrencyAmount 元素
        price_element = wait_for_element(page, "css:.CurrencyAmount", timeout=10)

        if not price_element:
            log.warning("未找到价格元素，假设价格正确")
            return True

        # 获取价格文本
        price_text = price_element.text.strip()
        log.info(f"检测到价格: {price_text}")

        # 检查价格是否为 0.00（支持 $0.00, US$0.00 等格式）
        if "0.00" in price_text and price_text.replace("US", "").replace("$", "").replace(" ", "").strip() == "0.00":
            log.success(f"✅ 价格正确: {price_text}")
            return True
        else:
            log.error(f"❌ 价格不正确: {price_text}，预期: $0.00 或 US$0.00")
            return False

    except Exception as e:
        log.error(f"检查价格时出错: {e}")
        return True  # 出错时假设价格正确，继续流程


def subscribe_team_plan(page, email: str, payment_info: Dict[str, str]) -> str:
    """订阅 Team 计划流程

    Args:
        page: 浏览器页面对象
        email: 邮箱地址
        payment_info: 支付信息

    Returns:
        str: "success", "price_not_zero", "failed"
    """
    try:
        log.separator()
        log.info("开始 Team 订阅流程", icon="credit_card")
        log.separator()

        # Step 1: 导航到 pricing 页面
        log.step("导航到 pricing 页面...")
        pricing_url = "https://chatgpt.com/#pricing"
        page.get(pricing_url)
        wait_for_page_stable(page, timeout=10)
        log_current_url(page, "Pricing 页面加载完成")

        # Step 2: 点击 "Claim free offer" 按钮
        log.step("查找并点击 'Claim free offer' 按钮...")
        claim_btn = wait_for_element(
            page,
            'css:button[data-testid="select-plan-button-teams-create"]',
            timeout=15,
        )

        if not claim_btn:
            log.error("未找到 'Claim free offer' 按钮")
            return "failed"

        human_delay(0.5, 1.0)
        claim_btn.click()
        log.success("已点击 'Claim free offer' 按钮")

        # 等待页面跳转到席位选择页面
        time.sleep(3)
        wait_for_page_stable(page, timeout=10)
        log_current_url(page, "席位选择页面")

        # Step 3: 点击 "Continue to billing" 按钮
        log.step("查找并点击 'Continue to billing' 按钮...")
        continue_btn = wait_for_element(page, "css:button.btn-green", timeout=15)

        if not continue_btn:
            # 尝试通过文本查找
            continue_btn = wait_for_element(page, "text:Continue to billing", timeout=5)

        if not continue_btn:
            log.error("未找到 'Continue to billing' 按钮")
            return "failed"

        human_delay(0.5, 1.0)
        continue_btn.click()
        log.success("已点击 'Continue to billing' 按钮")

        # 等待跳转到 Stripe 支付页面
        time.sleep(5)
        wait_for_page_stable(page, timeout=15)
        log_current_url(page, "Stripe 支付页面")

        # 检查价格是否为 $0.00
        if not check_payment_price(page):
            log.error("价格不为 $0.00，需要重试")
            return "price_not_zero"

        # Step 4: 填写 Stripe 支付表单
        if not fill_stripe_payment_form(page, payment_info):
            log.error("填写支付表单失败")
            return "failed"

        log.success("✅ Team 订阅流程完成")
        return "success"

    except Exception as e:
        log.error(f"Team 订阅流程异常: {e}")
        return "failed"


def fill_stripe_payment_form(page, payment_info: Dict[str, str]) -> bool:
    """填写 Stripe 支付表单

    Args:
        page: 浏览器页面对象
        payment_info: 支付信息字典

    Returns:
        bool: 是否成功填写
    """
    try:
        log.step("开始填写 Stripe 支付表单...")

        # 等待 Stripe iframe 加载
        time.sleep(3)

        # Step 0: 填写邮箱
        log.step("填写邮箱...")
        email_input = wait_for_element(page, 'css:input[name="email"]', timeout=10)

        if email_input:
            human_delay(0.3, 0.6)
            type_slowly(
                page, email_input, payment_info.get("email", "test@example.com")
            )
            log.success("邮箱已输入")
        else:
            log.warning("未找到邮箱输入框，跳过")

        # Step 1: 填写卡号
        log.step("填写卡号...")
        card_number_input = wait_for_element(
            page, 'css:input[name="cardNumber"]', timeout=15
        )

        if not card_number_input:
            card_number_input = wait_for_element(
                page, 'css:input[name="cardnumber"]', timeout=5
            )

        if not card_number_input:
            card_number_input = wait_for_element(
                page, 'css:input[placeholder*="Card number"]', timeout=5
            )

        if not card_number_input:
            log.error("未找到卡号输入框")
            return False

        human_delay(0.3, 0.6)
        type_slowly(page, card_number_input, payment_info["card_number"])
        log.success(f"卡号已输入: {payment_info['card_number']}")

        # Step 2: 填写有效期
        log.step("填写有效期...")
        expiry_input = wait_for_element(
            page, 'css:input[name="cardExpiry"]', timeout=10
        )

        if not expiry_input:
            expiry_input = wait_for_element(
                page, 'css:input[name="exp-date"]', timeout=5
            )

        if not expiry_input:
            expiry_input = wait_for_element(
                page, 'css:input[placeholder*="MM"]', timeout=5
            )

        if not expiry_input:
            log.error("未找到有效期输入框")
            return False

        human_delay(0.3, 0.6)
        type_slowly(page, expiry_input, payment_info["expiry"])
        log.success(f"有效期已输入: {payment_info['expiry']}")

        # Step 3: 填写 CVV
        log.step("填写 CVV...")
        cvv_input = wait_for_element(page, 'css:input[name="cardCvc"]', timeout=10)

        if not cvv_input:
            cvv_input = wait_for_element(page, 'css:input[name="cvc"]', timeout=5)

        if not cvv_input:
            cvv_input = wait_for_element(
                page, 'css:input[placeholder*="CVC"]', timeout=5
            )

        if not cvv_input:
            log.error("未找到 CVV 输入框")
            return False

        human_delay(0.3, 0.6)
        type_slowly(page, cvv_input, payment_info["cvv"])
        log.success(f"CVV 已输入: {payment_info['cvv']}")

        # Step 4: 填写账单地址
        if not fill_billing_address(page, payment_info):
            log.error("填写账单地址失败")
            return False

        # Step 5: 勾选确认框并提交
        if not submit_payment_form(page):
            log.error("提交支付表单失败")
            return False

        log.success("✅ Stripe 支付表单填写完成")
        return True

    except Exception as e:
        log.error(f"填写支付表单异常: {e}")
        return False


def fill_billing_address(page) -> bool:
    """填写账单地址并选择自动补全

    Args:
        page: 浏览器页面对象

    Returns:
        bool: 是否成功填写
    """
    try:
        log.step("填写账单姓名...")
        name_input = wait_for_element(page, 'css:input[name="billingName"]', timeout=10)

        if name_input:
            human_delay(0.3, 0.6)
            type_slowly(page, name_input, PAYMENT_INFO.get("billing_name", "John Doe"))
            log.success("账单姓名已输入")
        else:
            log.warning("未找到姓名输入框，跳过")

        log.step("填写账单地址...")
        address_input = wait_for_element(
            page, 'css:input[name="billingAddressLine1"]', timeout=10
        )

        if not address_input:
            address_input = wait_for_element(
                page, 'css:input[placeholder*="Address"]', timeout=5
            )

        if not address_input:
            log.error("未找到地址输入框")
            return False

        human_delay(0.3, 0.6)
        type_slowly(page, address_input, PAYMENT_INFO["billing_address"])
        log.success(f"地址已输入: {PAYMENT_INFO['billing_address']}")

        # 等待自动补全下拉框出现
        log.step("等待地址自动补全...")
        time.sleep(2)

        # 查找自动补全容器
        autocomplete_container = wait_for_element(
            page, "css:.AutocompleteInput-dropdown-container", timeout=5
        )

        if not autocomplete_container:
            log.warning("未找到自动补全下拉框，尝试验证地址是否已填充...")
            if verify_address_filled(page):
                return True
            else:
                log.warning("地址未自动填充，尝试手动填写地址...")
                return manual_fill_address(page)

        # 选择第一个选项
        log.step("选择第一个地址选项...")
        first_option = wait_for_element(
            page, "css:.AutocompleteInput-dropdown-container > *:first-child", timeout=5
        )

        if not first_option:
            log.warning("未找到第一个地址选项，尝试验证地址是否已填充...")
            if verify_address_filled(page):
                return True
            else:
                log.warning("地址未自动填充，尝试手动填写地址...")
                return manual_fill_address(page)

        human_delay(0.3, 0.6)
        first_option.click()
        log.success("已选择第一个地址选项")

        time.sleep(2)
        if verify_address_filled(page):
            return True
        else:
            log.warning("地址验证失败，尝试手动填写地址...")
            return manual_fill_address(page)

    except Exception as e:
        log.error(f"填写账单地址异常: {e}")
        return False


def submit_payment_form(page) -> bool:
    """勾选确认框并提交支付表单

    Args:
        page: 浏览器页面对象

    Returns:
        bool: 是否成功提交
    """
    try:
        log.step("查找并勾选确认框...")

        checkbox = wait_for_element(
            page, 'css:input[name="termsOfServiceConsentCheckbox"]', timeout=10
        )

        if not checkbox:
            checkbox = wait_for_element(page, 'css:input[type="checkbox"]', timeout=5)

        if checkbox:
            if not checkbox.states.is_selected:
                human_delay(0.3, 0.6)
                checkbox.click()
                log.success("已勾选确认框")
        else:
            log.warning("未找到确认框，尝试继续...")

        # 查找并点击 Subscribe 按钮
        log.step("查找并点击 'Subscribe' 按钮...")
        subscribe_btn = wait_for_element(page, 'css:button[type="submit"]', timeout=10)

        if not subscribe_btn:
            subscribe_btn = wait_for_element(page, "text:Subscribe", timeout=5)

        if not subscribe_btn:
            log.error("未找到 'Subscribe' 按钮")
            return False

        human_delay(0.5, 1.0)
        subscribe_btn.click()
        log.success("已点击 'Subscribe' 按钮")

        # 等待支付处理
        log.step("等待支付处理...")
        time.sleep(20)
        wait_for_page_stable(page, timeout=10)
        log_current_url(page, "支付处理后")

        # 检查是否跳转到成功页面
        current_url = page.url
        if "success-team" in current_url:
            log.success("✅ 已跳转到支付成功页面")
            return setup_workspace(page)

        # 如果未跳转，可能存在验证码，再等待30秒
        log.warning("页面未自动跳转到成功页面，可能存在验证码，继续等待...")
        time.sleep(30)
        wait_for_page_stable(page, timeout=10)
        current_url = page.url
        log_current_url(page, "验证后")

        if "success-team" in current_url:
            log.success("✅ 已跳转到支付成功页面")
            return setup_workspace(page)

        # 仍未跳转，需要用户确认
        log.separator()
        log.warning("⏸️  页面未自动跳转到成功页面")
        log.info("可能存在验证码或其他验证步骤")
        log.info("请在浏览器中完成验证，然后确认支付状态")
        log.separator()

        try:
            user_input = (
                input("\n👉 支付是否成功? (输入 'yes' 确认成功，其他输入表示失败): ")
                .strip()
                .lower()
            )

            if user_input in ["yes", "y", "success", "成功"]:
                log.success("✅ 用户确认支付成功")
                return setup_workspace(page)
            else:
                log.error(f"❌ 支付失败，用户输入: {user_input or '(空)'}")
                return False

        except (KeyboardInterrupt, EOFError):
            log.warning("\n用户中断")
            return False

    except Exception as e:
        log.error(f"提交支付表单异常: {e}")
        return False


def setup_workspace(page) -> bool:
    """设置工作空间名称

    在支付成功后，填写工作空间名称并完成设置
    """
    try:
        log.step("开始设置工作空间...")

        # 1. 点击第一个"继续"按钮
        log.step("查找并点击第一个'继续'按钮...")
        continue_btn = wait_for_element(page, "css:button.btn-primary", timeout=10)

        if not continue_btn:
            continue_btn = wait_for_element(page, "text:Continue", timeout=5)

        if not continue_btn:
            log.error("未找到继续按钮")
            return False

        human_delay(0.5, 1.0)
        continue_btn.click()
        log.success("已点击继续按钮")

        time.sleep(2)
        wait_for_page_stable(page, timeout=10)
        log_current_url(page, "点击继续后")

        # 2. 填写工作空间名称
        log.step("填写工作空间名称...")
        workspace_input = wait_for_element(
            page, 'css:input[name="workspace-name"]', timeout=10
        )

        if not workspace_input:
            log.error("未找到工作空间名称输入框")
            return False

        # 使用 input() 方法直接设置值（会自动清空）
        try:
            workspace_input.input("Codex")
            log.success("工作空间名称已输入: Codex")
        except Exception as e:
            log.error(f"输入工作空间名称失败: {e}")
            return False

        # 3. 点击第二个"继续"按钮
        log.step("查找并点击第二个'继续'按钮...")
        time.sleep(1)

        continue_btn2 = wait_for_element(page, "css:button.btn-primary", timeout=10)

        if not continue_btn2:
            continue_btn2 = wait_for_element(page, "text:Continue", timeout=5)

        if not continue_btn2:
            log.error("未找到第二个继续按钮")
            return False

        human_delay(0.5, 1.0)
        continue_btn2.click()
        log.success("已点击第二个继续按钮")

        time.sleep(2)
        wait_for_page_stable(page, timeout=10)
        log_current_url(page, "工作空间设置完成后")

        log.success("✅ 工作空间设置完成")
        return True

    except Exception as e:
        log.error(f"设置工作空间异常: {e}")
        return False


def save_team_info(email: str, password: str) -> bool:
    """保存team信息到team.json

    Args:
        email: 账号邮箱
        password: 账号密码

    Returns:
        是否保存成功
    """
    try:
        team_file = BASE_DIR / "team.json"

        # 读取现有的team.json
        if team_file.exists():
            with open(team_file, "r", encoding="utf-8") as f:
                teams = json.load(f)
        else:
            teams = []

        # 检查是否已存在该账号
        for team in teams:
            if isinstance(team, dict) and team.get("account") == email:
                log.warning(f"账号 {email} 已存在于 team.json 中，跳过保存")
                return True

        # 添加新的team信息
        new_team = {
            "account": email,
            "password": password,
            "expires_at": 0,
            "can_receive_verification_code": False
        }
        teams.append(new_team)

        # 保存到文件
        with open(team_file, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)

        log.success(f"✅ Team信息已保存到 {team_file}")
        return True

    except Exception as e:
        log.error(f"保存team信息失败: {e}")
        return False


def save_team_info_with_token(page, email: str, password: str) -> bool:
    """获取token并保存team信息到team.json

    Args:
        page: 浏览器页面对象
        email: 账号邮箱
        password: 账号密码

    Returns:
        是否保存成功
    """
    try:
        log.step("获取 Session 数据...")
        page.get("https://chatgpt.com/api/auth/session")
        time.sleep(2)

        # 获取页面内容（JSON）
        body = page.ele("tag:body", timeout=5)
        if not body:
            log.error("无法获取页面内容")
            return False

        text = body.text
        if not text or text == "{}":
            log.error("Session 数据为空")
            return False

        # 解析 JSON 数据
        data = json.loads(text)
        token = data.get("accessToken")
        account = data.get("account", {})
        account_id = account.get("id") if account else ""

        if not token:
            log.error("未获取到 accessToken")
            return False

        log.success(f"✅ 获取 token 成功")
        if account_id:
            log.info(f"  account_id: {account_id[:20]}...")

        # 保存到 team.json
        team_file = BASE_DIR / "team.json"

        # 读取现有的team.json
        if team_file.exists():
            with open(team_file, "r", encoding="utf-8") as f:
                teams = json.load(f)
        else:
            teams = []

        # 检查是否已存在该账号
        for team in teams:
            if isinstance(team, dict) and team.get("account") == email:
                log.warning(f"账号 {email} 已存在于 team.json 中，跳过保存")
                return True

        # 添加新的team信息（包含token）
        new_team = {
            "account": email,
            "password": password,
            "token": token,
            "account_id": account_id,
            "can_receive_verification_code": True
        }
        teams.append(new_team)

        # 保存到文件
        with open(team_file, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=2, ensure_ascii=False)

        log.success(f"✅ Team信息已保存到 {team_file}")
        return True

    except Exception as e:
        log.error(f"保存team信息失败: {e}")
        return False


def register_and_subscribe_account(account_info: Dict[str, str]) -> bool:
    """注册账号并订阅 Team

    Args:
        account_info: 账号信息字典

    Returns:
        bool: 是否成功
    """
    original_email = account_info["account"]
    password = account_info["password"]
    card_key_id = account_info.get("card_key_id")
    card_provider = account_info.get("card_provider", "holy")

    # 获取支付信息
    payment_info = get_payment_info(card_key_id, card_provider)
    if not payment_info:
        log.error("无法获取支付信息")
        return False

    # 最多尝试3次
    max_attempts = 3
    current_email = original_email

    for attempt in range(1, max_attempts + 1):
        log.separator()
        log.info(f"处理母号: {current_email} (尝试 {attempt}/{max_attempts})")
        log.separator()

        with browser_context() as page:
            # 注册账号
            result = register_openai_account(page, current_email, password)
            if result == "domain_blacklisted":
                log.error(f"域名被封禁: {current_email}")
                return False
            if not result:
                log.error(f"注册失败: {current_email}")
                return False

            log.success(f"✅ 注册成功: {current_email}")

            # 订阅 Team
            time.sleep(2)
            subscribe_result = subscribe_team_plan(page, current_email, payment_info)

            if subscribe_result == "success":
                log.success(f"✅ 母号处理完成: {current_email}")

                # 获取token并保存team信息
                if not save_team_info_with_token(page, current_email, password):
                    log.warning("Team信息保存失败，但流程已完成")

                return True

            elif subscribe_result == "price_not_zero":
                log.warning(f"价格不为 $0.00，尝试修改邮箱后重试")
                # 为邮箱添加后缀 n
                email_parts = current_email.split("@")
                if len(email_parts) == 2:
                    current_email = f"{email_parts[0]}n@{email_parts[1]}"
                    log.info(f"新邮箱: {current_email}")
                else:
                    log.error("邮箱格式错误，无法添加后缀")
                    return False

                # 如果不是最后一次尝试，继续循环
                if attempt < max_attempts:
                    continue
                else:
                    # 最后一次尝试也失败了
                    log.separator()
                    log.error(f"❌ 已尝试 {max_attempts} 次，价格始终不为 $0.00")
                    log.error(f"原始邮箱: {original_email}")
                    log.error(f"最后尝试的邮箱: {current_email}")
                    log.separator()
                    return False

            else:  # subscribe_result == "failed"
                log.error(f"Team 订阅失败: {current_email}")
                return False

    return False


def print_summary(total: int, success_count: int, failed_accounts: List[str]) -> None:
    log.header("处理完成")
    log.info(f"总计: {total} 个账号")
    log.success(f"成功: {success_count} 个")
    if failed_accounts:
        log.error(f"失败: {len(failed_accounts)} 个")
        log.error(f"失败账号: {', '.join(failed_accounts)}")


def main() -> int:
    log.header("母号注册 & Team 订阅脚本")

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
            if register_and_subscribe_account(account_info):
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
