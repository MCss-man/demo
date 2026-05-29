# Checklist

## Task 1: 重构 LLM Prompt 体系
- [x] prompt_templates.py 包含文件级、PR 级、风险检测级三层 Prompt 模板
- [x] llm_client.py 支持根据分析类型选择不同的 Prompt 模板
- [x] Prompt 模板设计合理，能引导 LLM 输出结构化 JSON 结果

## Task 2: 实现风险代码识别引擎
- [x] llm_analyzer.py 中 `analyze_risks()` 方法实现
- [x] llm_client.py 中 `analyze_risks()` 函数实现
- [x] 能够检测安全漏洞（SQL注入、XSS、路径遍历等）
- [x] 能够检测性能问题（N+1查询、内存泄漏等）
- [x] 能够检测代码异味（重复代码、过长函数等）
- [x] 每条风险结果包含置信度评分（高/中/低）

## Task 3: 实现上下文关联分析
- [x] llm_analyzer.py 中 `analyze_context()` 方法实现
- [x] llm_client.py 中 `analyze_context()` 函数实现
- [x] 能识别跨文件调用关系和依赖链
- [x] 能检测接口兼容性问题

## Task 4: 实现误报/漏报控制机制
- [x] 高风险项二次验证逻辑实现
- [x] 支持按置信度阈值过滤输出

## Task 5: 扩展 FastAPI API 端点
- [x] `GET /pr/{owner}/{repo}/{pr_number}/review` 端点实现
- [x] `GET /pr/{owner}/{repo}/{pr_number}/risks` 端点实现
- [x] `GET /pr/{owner}/{repo}/{pr_number}/summary` 端点实现
- [x] 新端点正确处理参数和错误情况

## Task 6: 扩展 CLI 工具
- [x] `--output json` 选项支持 JSON 格式输出
- [x] `--risk-only` 选项只输出风险检测结果
- [x] `--min-confidence` 选项设置置信度阈值
- [x] `--no-cache` 选项跳过缓存

## Task 7: 重构前端界面
- [x] 评审概览面板显示变更统计、风险分布、文件列表
- [x] 风险热力图可视化展示
- [x] 文件级评审详情展示（diff + Review 评论 + 风险标记）
- [x] 前端集成评审结果 API

## Task 8: 实现缓存机制
- [x] 基于文件/内存的缓存实现
- [x] 缓存键基于 PR 标识（owner/repo/pr_number）
- [x] API 端点集成缓存
- [x] CLI 工具支持 `--no-cache` 跳过缓存

## Task 9: 更新文档
- [x] README.md 更新新增功能说明
- [x] API 文档更新新端点说明
