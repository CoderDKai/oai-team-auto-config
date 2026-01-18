# 数据模型定义 (Data Model)

本文件定义注册与入库脚本涉及的核心实体及其约束。

## 1. 实体定义

### 1.1 Account
需要处理的账号信息。
- **email**: 账号邮箱
- **password**: 登录密码
- **metadata**: 额外信息（例如所属团队、标签）

### 1.2 Input Source
账号输入来源。
- **source_type**: `inline` 或 `file`
- **value**: 对应输入内容（内联参数或文件路径）

### 1.3 Execution Result
脚本输出结果。
- **status**: `success` 或 `failure`
- **message**: 结果说明或错误信息
- **records**: 每个账号的处理结果明细

## 2. 验证规则
- Account 必须包含 `account` 与 `password`。
- Input Source 的 `source_type` 只能为 `inline` 或 `file`，且 `value` 不可为空。
- Execution Result 必须包含总体状态与逐账号明细。

## 3. 输入映射
- 当 `source_type=inline` 时，`value` 为 JSON 字符串，解析得到 `Account` 列表。
- 当 `source_type=file` 时，`value` 为 JSON 文件路径，读取后得到 `Account` 列表。

## 4. 输出结构
- 统一输出包含 `status`、`message` 和 `records`。
- `records` 中每条记录至少包含 `account` 与处理结果状态。

## 5. 关系说明
- 一个 Input Source 可生成多个 Account。
- 每次脚本执行对应一个 Execution Result。
