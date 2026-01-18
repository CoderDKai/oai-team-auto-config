# 快速上手 (Quickstart)

本指南说明如何运行独立的注册与入库脚本。

## 1. 前置条件
- 准备配置文件与必要的账号输入数据。

## 2. 注册脚本

### 2.1 内联参数
```bash
python src/single/register_accounts.py --accounts "[{\"email\":\"user@example.com\",\"password\":\"Passw0rd!\"}]"
```

### 2.2 文件输入
```bash
python src/single/register_accounts.py --file accounts.json
```

## 3. 入库脚本

### 3.1 内联参数
```bash
python src/single/ingest_accounts.py --accounts "[{\"email\":\"user@example.com\",\"password\":\"Passw0rd!\"}]"
```

### 3.2 文件输入
```bash
python src/single/ingest_accounts.py --file accounts.json
```

## 4. 输出结果
脚本将输出每个账号的执行结果与失败原因，并汇总整体执行状态。
