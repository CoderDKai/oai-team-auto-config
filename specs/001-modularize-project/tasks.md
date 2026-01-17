---

description: "Task list for 项目模块化与工程化管理 implementation"
---

# Tasks: 项目模块化与工程化管理

**Input**: Design documents from `/specs/001-modularize-project/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 未在规格中要求测试任务，本计划不包含测试用例。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 创建模块化目录基础结构

- [x] T001 Create module directory structure in `src/` (`src/core/`, `src/automation/`, `src/team/`, `src/cpa/`, `src/crs/`, `src/s2a/`, `src/email/`, `src/cli/`)
- [x] T002 [P] Add package init files in `src/__init__.py` and each `src/*/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 基础能力与入口适配，阻塞所有用户故事

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Move shared utilities to core: `logger.py` → `src/core/logger.py`, `config.py` → `src/core/config.py`, `utils.py` → `src/core/utils.py`
- [x] T004 Update core import paths in `run.py` and any shared modules referencing `logger.py`, `config.py`, `utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 模块边界与责任清单 (Priority: P1) 🎯 MVP

**Goal**: 形成模块清单并完成现有代码的业务模块归属

**Independent Test**: 模块清单可覆盖全部既有功能，且新成员可在 10 分钟内定位模块

### Implementation for User Story 1

- [x] T005 [US1] Create module catalog with responsibilities and owners in `docs/modularization/module-catalog.md`
- [x] T006 [P] [US1] Move automation logic `browser_automation.py` → `src/automation/browser_automation.py`
- [x] T007 [P] [US1] Move team logic `team_service.py` → `src/team/team_service.py`
- [x] T008 [P] [US1] Move CPA logic `cpa_service.py` → `src/cpa/cpa_service.py`
- [x] T009 [P] [US1] Move CRS logic `crs_service.py` → `src/crs/crs_service.py`
- [x] T010 [P] [US1] Move S2A logic `s2a_service.py` → `src/s2a/s2a_service.py`
- [x] T011 [P] [US1] Move email logic `email_service.py` → `src/email/email_service.py`
- [x] T012 [US1] Update imports in `run.py` and moved modules to new `src/*` paths

**Checkpoint**: User Story 1 should be fully functional and independently verifiable

---

## Phase 4: User Story 2 - 模块依赖与协作规则 (Priority: P2)

**Goal**: 明确模块依赖规则与跨模块协作流程

**Independent Test**: 评审跨模块变更时能依据规则判断依赖是否合规

### Implementation for User Story 2

- [x] T013 [US2] Define dependency rules in `docs/modularization/dependency-rules.md`
- [x] T014 [US2] Add dependency review checklist in `docs/modularization/dependency-review.md`
- [x] T015 [US2] Document collaboration workflow in `docs/modularization/collaboration-workflow.md`

**Checkpoint**: User Story 2 rules can be applied in review independently

---

## Phase 5: User Story 3 - 模块化交付与变更管理 (Priority: P3)

**Goal**: 提供变更影响评估规则与交付管控方式

**Independent Test**: 能根据规则判断变更影响范围与协同模块

### Implementation for User Story 3

- [x] T016 [US3] Define change impact rules in `docs/modularization/change-impact.md`
- [x] T017 [US3] Provide change impact template in `docs/modularization/change-impact-template.md`

**Checkpoint**: User Story 3 rules can be applied independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事的收尾与文档连通

- [x] T018 [P] Link modularization docs from `README.md`
- [x] T019 [P] Add modularization overview in `docs/modularization/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 for rules documentation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2 for rules documentation

### Parallel Opportunities

- T002 can run in parallel with T001 once directories are created
- T006–T011 can run in parallel once core refactor (T003–T004) is complete
- Documentation tasks T013–T017 can proceed in parallel after Phase 2
- T018–T019 can run in parallel once all story docs exist

---

## Parallel Example: User Story 1

```bash
Task: "Move automation logic to src/automation/browser_automation.py"
Task: "Move CPA logic to src/cpa/cpa_service.py"
Task: "Move CRS logic to src/crs/crs_service.py"
Task: "Move S2A logic to src/s2a/s2a_service.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Define dependency rules in docs/modularization/dependency-rules.md"
Task: "Document collaboration workflow in docs/modularization/collaboration-workflow.md"
```

---

## Parallel Example: User Story 3

```bash
Task: "Define change impact rules in docs/modularization/change-impact.md"
Task: "Provide change impact template in docs/modularization/change-impact-template.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify module catalog and imports are aligned

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Validate independently
3. Add User Story 2 → Validate independently
4. Add User Story 3 → Validate independently

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. After Phase 2:
   - Developer A: User Story 1 implementation tasks
   - Developer B: User Story 2 documentation tasks
   - Developer C: User Story 3 documentation tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
