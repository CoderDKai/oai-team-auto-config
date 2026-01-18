---

description: "Task list for Split Registration And Ingest Scripts"
---

# Tasks: Split Registration And Ingest Scripts

**Input**: Design documents from `/specs/001-split-registration-ingest/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: 未在规格中要求测试任务，因此不生成测试任务。

**Organization**: 任务按用户故事组织，确保每个故事可独立实现与验证。

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 项目初始化与基础结构确认

- [ ] T001 盘点并确认现有 `src/single` 下相关脚本与入口位置（记录到 `specs/001-split-registration-ingest/tasks.md`）
- [ ] T002 [P] 统一脚本参数输入格式说明（用于 README 与 CLI 输出），记录在 `specs/001-split-registration-ingest/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有用户故事共享的前置能力

- [ ] T003 设计注册脚本与入库脚本的输入数据结构映射（inline/file），记录在 `specs/001-split-registration-ingest/data-model.md`
- [ ] T004 定义脚本运行结果的统一输出结构（success/failure/records），记录在 `specs/001-split-registration-ingest/data-model.md`

---

## Phase 3: User Story 1 - Run Registration Script Independently (Priority: P1) 🎯 MVP

**Goal**: 支持独立运行注册脚本，完成注册流程且不触发入库。

**Independent Test**: 运行注册脚本，提供合法参数后完成注册并输出结果，入库不被触发。

### Implementation for User Story 1

- [ ] T005 [US1] 新增独立注册脚本入口在 `src/single/register_accounts.py`
- [ ] T006 [P] [US1] 复用并抽取注册流程调用逻辑到 `src/automation/browser_automation.py`（如已存在则标注复用路径）
- [ ] T007 [US1] 实现注册脚本参数解析与校验在 `src/single/register_accounts.py`
- [ ] T008 [US1] 在注册脚本中输出逐账号执行结果与汇总状态 `src/single/register_accounts.py`

**Checkpoint**: 注册脚本可独立执行并返回可追踪结果。

---

## Phase 4: User Story 2 - Run Ingest Script Independently (Priority: P2)

**Goal**: 支持独立运行入库脚本，完成授权服务入库流程。

**Independent Test**: 运行入库脚本，提供合法参数后完成入库并输出结果。

### Implementation for User Story 2

- [ ] T009 [US2] 新增独立入库脚本入口在 `src/single/ingest_accounts.py`
- [ ] T010 [P] [US2] 复用现有入库服务调用逻辑（CRS/CPA/S2A）在 `src/crs/` `src/cpa/` `src/s2a/`
- [ ] T011 [US2] 实现入库脚本参数解析与校验在 `src/single/ingest_accounts.py`
- [ ] T012 [US2] 在入库脚本中输出逐账号执行结果与汇总状态 `src/single/ingest_accounts.py`

**Checkpoint**: 入库脚本可独立执行并返回可追踪结果。

---

## Phase 5: User Story 3 - Discover Usage In Single README (Priority: P3)

**Goal**: 在 `single` 目录提供 README，说明两个脚本用途与参数。

**Independent Test**: 打开 README 后可按示例命令执行两个脚本。

### Implementation for User Story 3

- [ ] T013 [US3] 编写 `src/single/README.md` 使用说明与示例命令
- [ ] T014 [US3] 在 README 中列出参数输入形式与注意事项 `src/single/README.md`

**Checkpoint**: README 提供清晰可执行的脚本用法。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事一致性与可维护性

- [ ] T015 [P] 更新 `specs/001-split-registration-ingest/quickstart.md` 与 README 保持一致
- [ ] T016 统一脚本日志与错误输出格式（stderr/stdout）在 `src/single/register_accounts.py` 与 `src/single/ingest_accounts.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖
- **Foundational (Phase 2)**: 依赖 Phase 1
- **User Stories (Phase 3-5)**: 依赖 Phase 2
- **Polish (Phase 6)**: 依赖完成目标用户故事

### User Story Dependencies

- **User Story 1 (P1)**: 无用户故事依赖
- **User Story 2 (P2)**: 无用户故事依赖
- **User Story 3 (P3)**: 依赖 US1/US2 已明确脚本命名与参数

### Parallel Opportunities

- Phase 1: T001 与 T002 可并行
- Phase 2: T003 与 T004 可并行
- US1: T005/T007/T008 顺序，T006 可并行准备
- US2: T009/T011/T012 顺序，T010 可并行准备
- US3: T013 与 T014 可并行
- Polish: T015 与 T016 可并行

---

## Parallel Example: User Story 1

```text
Task: "T005 [US1] 新增独立注册脚本入口在 src/single/register_accounts.py"
Task: "T006 [P] [US1] 复用并抽取注册流程调用逻辑到 src/automation/browser_automation.py"
```

---

## Parallel Example: User Story 2

```text
Task: "T009 [US2] 新增独立入库脚本入口在 src/single/ingest_accounts.py"
Task: "T010 [P] [US2] 复用现有入库服务调用逻辑在 src/crs/ src/cpa/ src/s2a/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1 与 Phase 2
2. 完成 User Story 1 并验证独立运行
3. 停止并验证输出结果

### Incremental Delivery

1. 完成 US1 → 独立验证
2. 完成 US2 → 独立验证
3. 完成 US3 → 独立验证

---

## Notes

- 所有任务均包含明确文件路径并符合检查清单格式。
- 未要求测试任务，故不包含测试相关步骤。
