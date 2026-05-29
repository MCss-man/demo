# AI Code Review Tool

帮助开发者提升 Pull Request 的 Review 效率与质量的 AI 辅助代码评审工具

## 功能特性

- **CLI 命令行工具**：快速获取 PR diff
- **FastAPI 服务**：提供 RESTful API 接口
- **Web 前端界面**：简洁的中文界面，支持 Diff 高亮显示
- **LLM 智能分析**：使用大语言模型对代码变更进行智能评审，提供修改总结和 3 条优化建议
- **多 LLM 支持**：支持 OpenAI、DeepSeek、阿里云 DashScope 等多种 LLM 提供商
- **支持认证**：支持 GitHub Token 认证，提高请求频率限制
- **SSL 灵活配置**：支持跳过 SSL 证书验证，适配特殊网络环境
- **自动重定向**：自动跟随 HTTP 重定向
- **风险代码识别**：检测安全漏洞、性能问题、代码异味
- **上下文关联分析**：跨文件影响范围分析
- **置信度评分**：多轮验证机制，控制误报率
- **完整评审面板**：可视化的评审结果展示
- **缓存机制**：提升重复请求响应速度

## 项目结构

```
demo1.0/
├── pyproject.toml          # 项目配置文件
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略规则
├── main.py                # FastAPI 启动入口
├── llm_client.py          # LLM 客户端（支持 OpenAI/DeepSeek/DashScope）
└── github_pr_diff/
    ├── __init__.py        # 包初始化
    ├── github_client.py   # GitHub API 客户端
    ├── cli.py             # CLI 命令行工具
    ├── llm_analyzer.py    # LLM 分析模块
    ├── cache.py           # 缓存管理模块
    └── api.py             # FastAPI 接口定义
```

## 安装

```bash
# 安装依赖
pip install fastapi httpx pydantic uvicorn python-dotenv typer openai

# 开发模式安装
pip install -e .
```

## 配置

### 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
GITHUB_TOKEN=your_github_personal_access_token

LLM_PROVIDER=openai
LLM_API_KEY=your_llm_api_key
```

### LLM 提供商配置

| 提供商 | Provider 值 | 默认模型 | Base URL |
|--------|-------------|----------|----------|
| OpenAI | `openai` | gpt-4o-mini | https://api.openai.com/v1 |
| DeepSeek | `deepseek` | deepseek-chat | https://api.deepseek.com |
| 阿里云 DashScope | `dashscope` 或 `qwen` | qwen-turbo | https://dashscope.aliyuncs.com/compatible-mode/v1 |

## 使用方法

### CLI 命令

```bash
# 基本用法
python -m github_pr_diff.cli <owner> <repo> <pr_number>

# 示例：获取 CPython 仓库的第 1 个 PR 的 diff
python -m github_pr_diff.cli python cpython 1

# 使用 Token
python -m github_pr_diff.cli fastapi fastapi 1000 --token ghp_your_token_here

# 跳过 SSL 证书验证
python -m github_pr_diff.cli python cpython 1 --skip-ssl

# 使用 LLM 分析代码变更
python -m github_pr_diff.cli python cpython 1 --analyze

# 查看帮助
python -m github_pr_diff.cli --help
```

### LLM 代码分析功能

使用大语言模型对 PR 的代码变更进行智能评审：

```bash
# 分析 PR diff，输出修改总结和 3 条优化建议
python -m github_pr_diff.cli python cpython 1 --analyze

# 输出示例：
# ================================================
# 📄 文件: main.py
# ================================================
# 📝 总结: 修改 hello 函数，添加返回值
# ================================================
# 💡 建议:
#   1. 建议1：添加单元测试验证返回值逻辑
#   2. 建议2：考虑添加类型注解
#   3. 建议3：建议添加文档字符串说明函数用途
```

### CLI 新增选项

```bash
# 输出 JSON 格式
python -m github_pr_diff.cli python cpython 1 --analyze --output json

# 仅显示风险
python -m github_pr_diff.cli python cpython 1 --analyze --risk-only

# 设置最低置信度
python -m github_pr_diff.cli python cpython 1 --analyze --min-confidence high

# 跳过缓存
python -m github_pr_diff.cli python cpython 1 --analyze --no-cache
```

### LLM Prompt 设计

LLM 分析采用专业的代码评审 Prompt：

- **System Prompt**: 设定为资深代码评审专家角色
- **User Prompt**: 提供文件信息和 diff 内容，要求：
  - 输出 15-25 字的简洁总结
  - 提供 3 条具体、可操作的改进建议
  - 强制 JSON 格式输出

### Web 前端界面

启动服务后访问首页：

```bash
python main.py
```

打开浏览器访问 `http://localhost:8000`

**界面特点**：
- 简洁的浅灰色背景
- 中文为主，技术术语保留英文
- Diff 结果语法高亮（新增行绿色、删除行红色）
- 支持跳过 SSL 证书验证

### FastAPI 服务

#### 启动服务

```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动。

#### API 接口

**GET 请求**

```bash
curl "http://localhost:8000/pr/{owner}/{repo}/{pr_number}?token=<your_token>"
```

**POST 请求**

```bash
curl -X POST "http://localhost:8000/pr/diff" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "fastapi",
    "repo": "fastapi",
    "pr_number": 1000,
    "token": "ghp_xxx"
  }'
```

#### API 新增端点

```bash
# 完整评审
curl "http://localhost:8000/pr/python/cpython/1/review"

# 仅风险检测
curl "http://localhost:8000/pr/python/cpython/1/risks"

# 仅 PR 摘要
curl "http://localhost:8000/pr/python/cpython/1/summary"

# 跳过缓存
curl "http://localhost:8000/pr/python/cpython/1/review?no_cache=true"
```

#### API 文档

启动服务后可访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

## 技术栈

- **Python**: 3.8+
- **FastAPI**: Web 框架
- **Typer**: CLI 框架
- **HTTPX**: HTTP 客户端
- **Pydantic**: 数据验证
- **Uvicorn**: ASGI 服务器
- **OpenAI**: LLM 客户端

## 许可证

MIT License
