# Tasks

- [x] Task 1: 重构 LLM Prompt 体系 - 设计多层次的 Prompt 模板（文件级、PR 级、风险检测级），提升分析准确性
  - [x] Subtask 1.1: 重设计 prompt_templates.py，新增文件级、PR 级、风险检测级 Prompt 模板
  - [x] Subtask 1.2: 优化 llm_client.py，支持不同分析类型的 Prompt 调用

- [x] Task 2: 实现风险代码识别引擎 - 检测安全漏洞、性能问题、代码异味
  - [x] Subtask 2.1: 在 llm_analyzer.py 中新增 `analyze_risks()` 方法
  - [x] Subtask 2.2: 在 llm_client.py 中新增 `analyze_risks()` 函数
  - [x] Subtask 2.3: 实现置信度评分机制

- [x] Task 3: 实现上下文关联分析 - 跨文件分析变更影响范围
  - [x] Subtask 3.1: 在 llm_analyzer.py 中新增 `analyze_context()` 方法
  - [x] Subtask 3.2: 在 llm_client.py 中新增 `analyze_context()` 函数
  - [x] Subtask 3.3: 实现跨文件依赖关系检测

- [x] Task 4: 实现误报/漏报控制机制 - 多轮验证 + 分级输出
  - [x] Subtask 4.1: 实现高风险项二次验证逻辑
  - [x] Subtask 4.2: 实现分级输出过滤

- [x] Task 5: 扩展 FastAPI API 端点 - 新增评审、风险、摘要端点
  - [x] Subtask 5.1: 新增 `GET /pr/{owner}/{repo}/{pr_number}/review` 端点
  - [x] Subtask 5.2: 新增 `GET /pr/{owner}/{repo}/{pr_number}/risks` 端点
  - [x] Subtask 5.3: 新增 `GET /pr/{owner}/{repo}/{pr_number}/summary` 端点

- [x] Task 6: 扩展 CLI 工具 - 新增命令行选项
  - [x] Subtask 6.1: 新增 `--output`, `--risk-only`, `--min-confidence` 等选项
  - [x] Subtask 6.2: 支持 JSON 结构化输出

- [x] Task 7: 重构前端界面 - 从纯 Diff 展示升级为完整的 Code Review 面板
  - [x] Subtask 7.1: 设计评审概览面板布局
  - [x] Subtask 7.2: 实现风险热力图可视化
  - [x] Subtask 7.3: 实现文件级评审详情展示
  - [x] Subtask 7.4: 集成评审结果 API

- [x] Task 8: 实现缓存机制 - 对已分析的 PR 结果进行缓存
  - [x] Subtask 8.1: 实现基于文件/内存的缓存
  - [x] Subtask 8.2: 集成缓存到 API 和 CLI

- [x] Task 9: 更新文档 - 更新 README 和注释
  - [x] Subtask 9.1: 更新 README.md 新增功能说明
  - [x] Subtask 9.2: 更新 API 文档

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2, Task 3]
- [Task 5] depends on [Task 2, Task 3, Task 8]
- [Task 6] depends on [Task 2, Task 3, Task 4]
- [Task 7] depends on [Task 5]
- [Task 8] 独立
- [Task 9] depends on [Task 2, Task 3, Task 5, Task 6, Task 7, Task 8]
