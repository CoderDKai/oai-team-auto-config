# 批量账号添加工具

独立的批量账号添加脚本，支持将 OpenAI 账号批量注册并添加到授权服务（CRS/CPA/S2A）。

## 特点

- ✅ 不依赖 `team.json` 配置
- ✅ 支持所有三种授权服务（CRS/CPA/S2A）
- ✅ 自动注册未注册的账号
- ✅ 自动处理验证码
- ✅ 完整的授权流程

## 使用方法

### 方式1: 从命令行传入

```bash
python src/single/batch_add_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
```

### 方式2: 从文件读取

1. 创建账号文件：

```bash
cp src/single/batch_accounts.json.example batch_accounts.json
```

2. 编辑文件填入真实账号：

```json
[
  {
    "account": "user1@example.com",
    "password": "YourPassword123!"
  },
  {
    "account": "user2@example.com",
    "password": "YourPassword456!"
  }
]
```

3. 运行脚本：

```bash
python src/single/batch_add_accounts.py --file batch_accounts.json
```

## 配置要求

在 `config.toml` 中配置授权服务：

```toml
auth_provider = "s2a"

[s2a]
api_base = "https://your-sub2api-service.com/api/v1"
admin_key = "your-admin-api-key"
```

## 工作流程

```
验证授权服务连接
    ↓
加载账号列表
    ↓
逐个处理账号
    ├─ 注册 OpenAI 账号
    ├─ 执行授权流程
    └─ 添加到授权服务
    ↓
打印处理结果
```

## 输出示例

```
============================================================
批量账号添加工具
授权服务: S2A
============================================================

✓ S2A 服务连接成功
✓ 成功加载 2 个账号

进度: 1/2
============================================================
处理账号: user1@example.com
============================================================

✓ ✅ 账号添加成功: user1@example.com

进度: 2/2
============================================================
处理账号: user2@example.com
============================================================

✓ ✅ 账号添加成功: user2@example.com

============================================================
处理完成
============================================================
总计: 2 个账号
✓ 成功: 2 个
============================================================
```

## 注意事项

1. 确保 `config.toml` 中的授权服务配置正确
2. 账号格式必须包含 `account` 和 `password` 字段
3. 需要能够接收账号邮箱的验证码
4. 需要安装 Chrome 浏览器

## 相关文档

- [项目主 README](../../README.md)
- [S2A 专用脚本](add_accounts_to_s2a.py)
