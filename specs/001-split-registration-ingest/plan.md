# Implementation Plan: Split Registration And Ingest Scripts

**Branch**: `001-split-registration-ingest` | **Date**: 2026-01-18 | **Spec**: specs/001-split-registration-ingest/spec.md
**Input**: Feature specification from `/specs/001-split-registration-ingest/spec.md`

## Summary

将现有流程拆分为独立的注册脚本与入库脚本，统一放置在 `single` 目录，并补齐该目录 README 用法说明。研究结论强调沿用现有 `argparse` 模式与脚本组织惯例。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: drissionpage, requests, rich, tomli, setuptools  
**Storage**: 文件（如 accounts.csv、team_tracker.json）  
**Testing**: pytest  
**Target Platform**: Linux  
**Project Type**: single  
**Performance Goals**: 批量处理单次运行在 5 分钟内完成（与规模相关）  
**Constraints**: 现有流程需可拆分且不破坏主流程  
**Scale/Scope**: 批量账号脚本级处理（数量级依赖输入规模）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Constitution 文件为模板占位内容，无法据此判断具体门禁要求；当前无显式门禁可验证，需后续补充。

## Project Structure

### Documentation (this feature)

```text
specs/001-split-registration-ingest/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── automation/
├── single/
├── crs/
├── cpa/
├── s2a/
├── utils/
└── ...

tests/
```

**Structure Decision**: 单体 Python 项目，脚本入口集中在 `src/single`，保留现有结构并新增独立脚本与 README。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无
