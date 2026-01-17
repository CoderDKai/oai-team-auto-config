# Data Model: 项目模块化与工程化管理

## Entity: 模块

- **Fields**: 名称、职责范围、边界说明
- **Relationships**: 关联模块负责人、依赖规则、变更影响
- **Validation**: 必须覆盖项目已有功能；职责与边界描述清晰可辨

## Entity: 模块负责人

- **Fields**: 负责人名称/团队、联系方式（可选）
- **Relationships**: 关联模块
- **Validation**: 每个模块必须有明确负责人或负责团队

## Entity: 依赖规则

- **Fields**: 允许依赖、禁止依赖、依赖方向
- **Relationships**: 作用于模块间关系
- **Validation**: 必须明确禁止循环依赖并可用于评审判定

## Entity: 变更影响

- **Fields**: 影响类型、涉及模块、协作要求
- **Relationships**: 关联模块与依赖规则
- **Validation**: 必须支持判断是否需要其他模块协作或同步
