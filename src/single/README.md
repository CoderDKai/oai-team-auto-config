# single 脚本说明

该目录包含独立运行的脚本入口，支持将流程拆分为注册与入库两类操作，并保留 S2A 专用脚本。

## 通用账号输入格式

支持两种输入方式：
- `--accounts`：JSON 字符串
- `--file`：JSON 文件路径

账号结构示例：
```json
[
  {
    "account": "user@example.com",
    "password": "Passw0rd!"
  }
]
```

## 脚本列表与用法

### 1. 注册脚本

用于独立执行注册流程，不触发入库。

```bash
python src/single/register_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
```

```bash
python src/single/register_accounts.py --file accounts.json
```

### 2. 入库脚本

用于独立执行入库流程，按配置将账号入库至 CRS/CPA/S2A。

```bash
python src/single/ingest_accounts.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
```

```bash
python src/single/ingest_accounts.py --file accounts.json
```

### 3. S2A 专用脚本（保留）

用于批量将账号添加到 S2A（包含注册/授权完整流程）。

```bash
python src/single/add_accounts_to_s2a.py --accounts '[{"account":"test@example.com","password":"test@123"}]'
```

```bash
python src/single/add_accounts_to_s2a.py --file accounts.json
```

## 前置要求

1. **配置授权服务**

在 `config.toml` 中设置 `auth_provider` 与对应服务配置（CRS/CPA/S2A）。

2. **准备接收验证码的邮箱**

注册或授权流程可能需要验证码，请确保邮箱可接收。

## 注意事项

1. 账号数据必须包含 `account` 与 `password` 字段
2. `config.toml` 配置错误会导致连接失败
3. 脚本执行过程中支持手动输入验证码

## 相关文档

- [项目主README](../../README.md)
- [S2A服务文档](https://github.com/Wei-Shaw/sub2api)
