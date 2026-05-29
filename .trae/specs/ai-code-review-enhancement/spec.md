# AI 代码评审工具 Spec

## Why

现有工具仅提供基础的 PR diff 获取和简单的 LLM 分析（每个文件给出总结+3条建议），缺乏风险代码智能识别、上下文关联分析、误报漏报控制机制，以及完善的前端交互体验。开发者无法高效利用 AI 辅助完成高质量的代码评审。

## What Changes

- **重构 LLM Prompt 体系**：设计多层次的 Prompt（文件级 vs PR 级 vs 风险检测级），提升分析准确性
- **新增风险代码识别引擎**：基于 LLM 检测安全漏洞、性能问题、代码异味等风险
- **新增上下文关联分析**：跨文件分析变更影响范围，识别潜在连锁影响
- **新增误报/漏报控制机制**：多轮验证 + 置信度评分 + 分级输出
- **重构前端界面**：从纯 Diff 展示升级为完整的 Code Review 面板
- **新增 CI/CD 集成支持**：提供 GitHub Action 集成指南和 API 端点
- **新增缓存机制**：对已分析的 PR 结果进行缓存，提升重复请求响应速度
- **优化 CLI 输出格式**：支持结构化输出（JSON）和格式化表格输出

## Impact

- Affected specs: 所有现有功能模块
- Affected code: 
  - `llm_client.py` - Prompt 体系重构
  - `llm_analyzer.py` - 新增风险检测、上下文分析
  - `api.py` - 新增 API 端点
  - `cli.py` - 新增命令行选项
  - `static/index.html` - 前端全面重构
  - `prompt_templates.py` - Prompt 模板重设计
  - `pyproject.toml` - 可能新增依赖

## ADDED Requirements

### Requirement: 风险代码识别引擎
The system SHALL provide risk code identification across multiple dimensions.

#### Scenario: 安全漏洞检测
- **WHEN** PR diff 包含 SQL 注入、XSS、路径遍历等安全风险
- **THEN** 系统标记为"高危"，并给出具体说明和修复建议

#### Scenario: 性能问题检测
- **WHEN** PR diff 包含 N+1 查询、内存泄漏、不必要的循环等性能问题
- **THEN** 系统标记为"中危"，并给出优化建议

#### Scenario: 代码异味检测
- **WHEN** PR diff 包含重复代码、过长函数、不恰当命名等问题
- **THEN** 系统标记为"低危"，并给出改进建议

### Requirement: 上下文关联分析
The system SHALL analyze cross-file impact and dependencies.

#### Scenario: 跨文件变更影响分析
- **WHEN** PR 包含多个文件的变更
- **THEN** 系统分析变更文件之间的调用关系和依赖链，识别潜在影响范围

#### Scenario: 接口兼容性检查
- **WHEN** PR 修改了公共 API、函数签名或数据结构
- **THEN** 系统检测调用方是否同步更新，标记不兼容的变更

### Requirement: 误报/漏报控制
The system SHALL implement false positive/negative control mechanisms.

#### Scenario: 置信度评分
- **WHEN** 系统生成每条分析结果
- **THEN** 附带置信度评分（高/中/低），帮助开发者区分可靠发现和需人工判断的项

#### Scenario: 多轮验证
- **WHEN** 系统检测到高风险项
- **THEN** 通过二次查询 LLM 进行验证，降低误报率

### Requirement: PR 评审总结面板
The system SHALL provide a comprehensive PR review dashboard.

#### Scenario: 评审概览
- **WHEN** 用户查看 PR 评审结果
- **THEN** 显示变更统计、风险分布、文件列表、总体评分

#### Scenario: 文件级评审详情
- **WHEN** 用户点击某个文件
- **THEN** 显示该文件的 diff、逐行的 Review 评论、风险标记

#### Scenario: 风险热力图
- **WHEN** 风险分析完成
- **THEN** 以可视化方式展示各文件/各类型的风险分布

### Requirement: 缓存机制
The system SHALL cache analysis results for performance.

#### Scenario: 结果复用
- **WHEN** 同一 PR 被重复分析
- **THEN** 返回缓存结果，跳过 LLM 调用

## MODIFIED Requirements

### Requirement: LLM 分析模块重构
原有简单的单文件分析升级为多层次分析体系：

- **文件级分析**：分析单个文件的变更（保持原有功能，增强 Prompt 质量）
- **PR 级概览分析**：分析整个 PR 的变更目标和影响范围
- **风险扫描**：专项检测安全、性能、代码质量风险
- **上下文分析**：跨文件关联分析

### Requirement: CLI 工具增强
原有 CLI 新增选项：

- `--output json`：输出 JSON 格式结果
- `--risk-only`：仅输出风险检测结果
- `--min-confidence low|medium|high`：设置最低置信度阈值
- `--no-cache`：跳过缓存，强制重新分析

### Requirement: API 端点扩展
在原有 API 基础上新增：

- `GET /pr/{owner}/{repo}/{pr_number}/review`：完整评审结果
- `GET /pr/{owner}/{repo}/{pr_number}/risks`：仅风险检测结果
- `GET /pr/{owner}/{repo}/{pr_number}/summary`：仅 PR 概览
- 所有新端点支持 `format=json` 参数

## REMOVED Requirements
无
