# 母号注册与 Team 订阅脚本使用说明

## 📋 功能说明

`register_parent_accounts.py` 是一个自动化脚本，用于：
1. 批量注册 OpenAI 账号（母号）
2. 自动订阅 ChatGPT Team 计划（使用测试卡）

## 🚀 使用方法

### 方法 1: 从 JSON 文件读取账号

```bash
python src/single/register_parent_accounts.py --file test_parent_accounts.json
```

### 方法 2: 直接传入账号（JSON 格式）

```bash
python src/single/register_parent_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
```

## 📝 账号文件格式

创建一个 JSON 文件（例如 `test_parent_accounts.json`）：

```json
[
  {
    "account": "parent1@example.com",
    "password": "SecurePassword123!"
  },
  {
    "account": "parent2@example.com",
    "password": "SecurePassword456!"
  }
]
```

## 🔄 完整流程

脚本会自动执行以下步骤：

### 第一阶段：账号注册
1. 打开 ChatGPT 注册页面
2. 输入邮箱和密码
3. 获取并输入邮箱验证码
4. 填写个人信息（姓名、生日）
5. 完成注册

### 第二阶段：Team 订阅
1. 导航到 `https://chatgpt.com/#pricing`
2. 点击 "Claim free offer" 按钮
3. 在席位选择页面点击 "Continue to billing"
4. 填写 Stripe 支付表单：
   - 卡号：5481087156231015
   - 有效期：01/32
   - CVV：214
   - 账单地址：2792 BASCOM CORNER RD,RISING SUN,IN 47040
5. 选择地址自动补全的第一个选项
6. 勾选确认框
7. 点击 "Subscribe" 提交订阅

## ⚙️ 支付信息配置

默认使用的测试卡信息（在脚本中的 `PAYMENT_INFO` 常量）：

```python
PAYMENT_INFO = {
    "card_number": "5481087156231015",
    "expiry": "01/32",
    "cvv": "214",
    "billing_address": "2792 BASCOM CORNER RD,RISING SUN,IN 47040",
}
```

如需修改，请编辑脚本中的这个配置。

## 📊 输出示例

```
==================== 母号注册 & Team 订阅脚本 ====================
✅ 成功加载 2 个账号

进度: 1/2
==================== 处理母号: parent1@example.com ====================
🌐 开始注册 OpenAI 账号: parent1@example.com
✅ 注册成功: parent1@example.com

==================== 开始 Team 订阅流程 ====================
📍 导航到 pricing 页面...
✅ 已点击 'Claim free offer' 按钮
✅ 已点击 'Continue to billing' 按钮
✅ Stripe 支付表单填写完成
✅ 母号处理完成: parent1@example.com

==================== 处理完成 ====================
总计: 2 个账号
成功: 2 个
```

## ⚠️ 注意事项

1. **浏览器模式**：脚本使用项目配置的浏览器设置（在 `config.toml` 中配置）
2. **等待时间**：各步骤之间有适当延迟，模拟真人操作
3. **错误处理**：如果某个步骤失败，会记录错误并继续处理下一个账号
4. **测试卡**：默认使用的是测试卡信息，实际使用时请替换为真实卡信息

## 🔍 故障排查

### 问题：找不到按钮或元素
- 检查网页是否正常加载
- 确认 ChatGPT 页面结构是否有变化
- 查看日志中的 URL 信息

### 问题：支付表单填写失败
- 确认 Stripe iframe 是否加载完成
- 检查元素选择器是否正确
- 查看是否有弹窗或验证码

### 问题：地址自动补全不工作
- 确认输入的地址格式正确
- 等待时间可能需要调整
- 检查自动补全下拉框是否出现

## 📁 相关文件

- `src/single/register_parent_accounts.py` - 主脚本
- `src/automation/browser_automation.py` - 浏览器自动化模块
- `test_parent_accounts.json.example` - 示例账号文件
