# AI Code Review Tool

帮助开发者提升 Pull Request 的 Review 效率与质量的 AI 辅助代码评审工具

## 功能特性

- **GitHub PR 获取**：通过 GitHub API 获取 PR 代码变更（Diff）
- **文件类型智能识别**：自动区分代码文件、文档文件、二进制文件
  - **代码文件**：深度分析（检测 bug、安全漏洞、性能问题、代码异味）
  - **文档文件**：简单总结（变更摘要）
  - **二进制文件**：跳过分析（节省 API 调用）
- **CLI 命令行工具**：快速获取 PR diff 并进行智能分析
- **FastAPI 服务**：提供 RESTful API 接口
- **现代化 Web 前端界面**：美观的中文界面，深色主题，支持 Diff 高亮显示
- **LLM 智能分析**：使用大语言模型对代码变更进行全面评审
  - 单文件分析：提供修改总结和优化建议
  - PR 概览分析：整体变更摘要、关键变更点
  - 风险检测：安全漏洞、性能问题、代码异味识别
  - 上下文关联分析：跨文件影响范围分析
  - 高置信度风险二次验证机制
- **默认支持阿里云 DashScope**：默认配置阿里云通义千问模型
- **支持认证**：支持 GitHub Token 认证，提高请求频率限制
- **SSL 灵活配置**：支持跳过 SSL 证书验证，适配特殊网络环境
- **完整的可视化评审**：风险热力图、统计概览、详情展示
- **缓存机制**：提升重复请求响应速度

## 支持的文件类型

### 代码文件（深度分析）

支持 30+ 种编程语言，包括：
- **后端语言**：Python, Java, JavaScript, TypeScript, Go, Rust, Ruby, PHP, C/C++, C#, Scala, Kotlin
- **Web 前端**：HTML, CSS, SCSS, Vue, React, Svelte
- **移动端**：Swift, Kotlin
- **脚本语言**：Shell (Bash/Zsh/Fish), PowerShell, Batch
- **配置格式**：JSON, YAML, TOML, XML, INI, ENV
- **数据库**：SQL
- **其他**：Makefile, Dockerfile, Markdown 等

### 文档文件（简单总结）

`.txt`, `.doc`, `.docx`, `.rst`, `.adoc` 等

### 二进制文件（跳过分析）

`.png`, `.jpg`, `.pdf`, `.zip` 等（不调用 API，节省资源）

## 项目结构

```
demo1.0/
├── pyproject.toml          # 项目配置文件
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略规则
├── main.py                # FastAPI 启动入口
├── llm_client.py          # LLM 客户端（默认阿里云 DashScope）
├── prompt_templates.py    # LLM 提示词模板
├── static/
│   └── index.html         # Web 前端界面（中文）
└── github_pr_diff/
    ├── __init__.py        # 包初始化
    ├── github_client.py   # GitHub API 客户端
    ├── cli.py             # CLI 命令行工具
    ├── llm_analyzer.py    # LLM 分析模块
    ├── cache.py           # 缓存管理模块
    ├── file_utils.py      # 文件类型识别工具
    └── api.py             # FastAPI 接口定义
```

## 安装

```bash
# 安装依赖
pip install fastapi httpx pydantic uvicorn python-dotenv typer openai rich

# 开发模式安装
pip install -e .
```

## 配置

### 环境变量

复制 `.env.example` 为 `.env`（可选，当前项目默认已配置）：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
GITHUB_TOKEN=your_github_personal_access_token
```

### LLM 配置

项目默认使用阿里云 DashScope，配置在 `llm_client.py` 中：
- 默认 API Key：已内置测试密钥
- 默认模型：qwen-turbo
- Base URL：https://dashscope.aliyuncs.com/compatible-mode/v1

如需修改，可编辑 `llm_client.py` 中的 `DEFAULT_API_KEY`、`DEFAULT_BASE_URL`、`DEFAULT_MODEL` 常量。

## 使用方法

### Web 前端界面

```bash
python main.py
```

打开浏览器访问 `http://localhost:8000`

**界面特点**：
- 中文界面
- 深色主题
- PR 信息输入
- 概览统计卡片
- 风险热力图（按文件显示风险级别）
- PR 摘要展示
- 风险列表（支持按类型和置信度筛选）
- 修改文件详情（含 Diff 高亮和文件级建议）
- 上下文关联分析展示

### CLI 命令

```bash
# 基本用法 - 获取 PR diff
python -m github_pr_diff.cli diff <owner> <repo> <pr_number>

# 示例：获取 FastAPI 仓库的第 1000 个 PR 的 diff
python -m github_pr_diff.cli diff fastapi fastapi 1000

# 使用 Token
python -m github_pr_diff.cli diff fastapi fastapi 1000 --token ghp_your_token_here

# 跳过 SSL 证书验证
python -m github_pr_diff.cli diff fastapi fastapi 1000 --skip-ssl

# 使用 LLM 进行完整代码评审
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze

# 仅检测风险
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze --risk-only

# 设置最低置信度
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze --min-confidence high

# 输出 JSON 格式
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze --output json

# 跳过缓存强制重新分析
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze --no-cache

# 指定 LLM API Key
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze --llm-key sk-xxx

# 查看帮助
python -m github_pr_diff.cli --help
```

### LLM 代码分析功能

使用大语言模型对 PR 的代码变更进行智能评审：

```bash
# 分析 PR diff，输出完整评审报告
python -m github_pr_diff.cli diff fastapi fastapi 1000 --analyze

# 输出包含：
# - Diff 统计信息（文件数、新增/删除行数）
# - PR 标题和变更摘要
# - 关键变更点列表
# - 风险评估和总体建议
# - 风险检测结果（按严重程度排序）
# - 上下文关联分析
```

### FastAPI 服务

#### 启动服务

```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动。

#### API 接口

**获取 PR Diff（GET）**

```bash
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}?token=<your_token>&skip_ssl=true"
```

**获取 PR Diff（POST）**

```bash
curl -X POST "http://localhost:8000/pr/diff" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "fastapi",
    "repo": "fastapi",
    "pr_number": 1000,
    "token": "ghp_xxx",
    "skip_ssl": false
  }'
```

**完整代码评审**

```bash
# GET 请求
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}/review?token=<your_token>&llm_key=<your_llm_key>&min_confidence=medium&no_cache=false"

# POST 请求
curl -X POST "http://localhost:8000/pr/review" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "fastapi",
    "repo": "fastapi",
    "pr_number": 1000,
    "token": "ghp_xxx",
    "llm_key": "sk-xxx",
    "min_confidence": "low"
  }'
```

**仅风险检测**

```bash
# GET 请求
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}/risks"

# POST 请求
curl -X POST "http://localhost:8000/pr/risks" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**仅 PR 摘要**

```bash
# GET 请求
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}/summary"

# POST 请求
curl -X POST "http://localhost:8000/pr/summary" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**基础分析**

```bash
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}/analyze"
```

#### API 文档

启动服务后可访问：
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 依赖说明

核心依赖：
- fastapi: Web 框架
- httpx: HTTP 客户端
- pydantic: 数据验证
- uvicorn: ASGI 服务器
- typer: CLI 框架
- openai: OpenAI 兼容 API 客户端
- python-dotenv: 环境变量管理
- rich: CLI 美化输出

## 注意事项

1. **公共仓库**：无需 Token 也可访问，但有请求频率限制（60次/小时）
2. **私有仓库**：必须提供 Token
3. **频率限制**：使用 Token 后请求频率限制更高（5000次/小时）
4. **Token 安全**：请勿将 Token 提交到版本控制系统
5. **SSL 证书**：默认启用 SSL 验证，特殊网络环境可使用 `--skip-ssl` 参数跳过
6. **PR 状态**：只能获取存在的 PR 的 diff，已删除或合并的 PR 会返回 404
7. **LLM 配额**：注意 LLM API 的调用配额和费用
8. **代码分析优先**：项目核心是代码分析功能，二进制文件和纯文档文件会自动跳过分析

## 技术栈

- **Python**：3.8+
- **FastAPI**：Web 框架
- **Typer**：CLI 框架
- **HTTPX**：HTTP 客户端
- **Pydantic**：数据验证
- **Uvicorn**：ASGI 服务器
- **OpenAI SDK**：LLM 客户端（兼容 DashScope）
- **阿里云 DashScope**：默认 LLM 提供商
- **Rich**：CLI 美化

## 许可证

MIT License