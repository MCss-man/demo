# GitHub PR Diff Tool

一个基于 Python + FastAPI/CLI 的工具，用于获取 GitHub Pull Request 的 diff 内容。

## 功能特性

- **CLI 命令行工具**：快速获取 PR diff
- **FastAPI 服务**：提供 RESTful API 接口
- **Web 前端界面**：美观的中文界面，支持 Diff 高亮显示
- **LLM 智能分析**：使用大语言模型对代码变更进行智能评审，提供修改总结和优化建议
- **支持认证**：支持 GitHub Token 认证，提高请求频率限制
- **SSL 灵活配置**：支持跳过 SSL 证书验证，适配特殊网络环境
- **自动重定向**：自动跟随 HTTP 重定向
- **简洁易用**：简单的命令和 API 设计

## 项目结构

```
demo1.0/
├── pyproject.toml          # 项目配置文件
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略规则
├── main.py                # FastAPI 启动入口
└── github_pr_diff/
    ├── __init__.py        # 包初始化
    ├── github_client.py   # GitHub API 客户端
    ├── cli.py             # CLI 命令行工具
    └── api.py             # FastAPI 接口定义
```

## 安装

```bash
# 安装依赖
pip install fastapi httpx pydantic uvicorn python-dotenv typer

# 开发模式安装
pip install -e .
```

## 配置

### 方式一：环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 GitHub Token：

```env
GITHUB_TOKEN=your_github_personal_access_token
```

### 方式二：命令行参数

在使用 CLI 或 API 时直接传入 `--token` 参数。

## 使用方法

### CLI 命令

```bash
# 基本用法
python -m github_pr_diff.cli <owner> <repo> <pr_number>

# 示例：获取 CPython 仓库的第 1 个 PR 的 diff
python -m github_pr_diff.cli python cpython 1

# 使用 Token
python -m github_pr_diff.cli fastapi fastapi 1000 --token ghp_your_token_here

# 跳过 SSL 证书验证（用于特殊网络环境）
python -m github_pr_diff.cli python cpython 1 --skip-ssl

# 使用 LLM 分析代码变更（需配置阿里云 DashScope API Key）
python -m github_pr_diff.cli python cpython 1 --analyze --llm-key sk-your-dashscope-key

# 查看帮助
python -m github_pr_diff.cli --help
```

#### LLM 代码分析功能

使用大语言模型对 PR 的代码变更进行智能评审：

```bash
# 分析 PR diff，输出修改总结和优化建议
python -m github_pr_diff.cli python cpython 1 --analyze --llm-key sk-xxx

# 输出示例：
# 文件 1: Doc/tools/extensions/pyspecific.py
#   总结: 修改代码逻辑
#   建议:
#     1. 建议检查新代码是否与旧代码功能一致
#     2. 建议添加注释说明修改原因
#     3. 建议进行单元测试验证修改后的行为
```

#### CLI 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| owner | TEXT | 是 | GitHub 仓库所有者 |
| repo | TEXT | 是 | GitHub 仓库名称 |
| pr_number | INTEGER | 是 | Pull Request 编号 |
| --token | TEXT | 否 | GitHub 个人访问令牌 |
| --skip-ssl | BOOLEAN | 否 | 跳过 SSL 证书验证 |

### Web 前端界面

启动服务后访问首页即可使用中文界面：

```bash
python main.py
```

打开浏览器访问 `http://localhost:8000`

**界面特点**：
- 中文为主，技术术语保留英文（如 Owner、Repo、Token）
- 美观的渐变背景和卡片式布局
- Diff 结果语法高亮（新增行绿色、删除行红色）
- 支持跳过 SSL 证书验证选项

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

# 示例
curl "http://localhost:8000/pr/fastapi/fastapi/1000?token=ghp_xxx"
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

#### API 响应示例

```json
{
  "owner": "fastapi",
  "repo": "fastapi",
  "pr_number": 1000,
  "diff": "diff --git a/file1.py b/file1.py\nindex abc123..def456 100644\n--- a/file1.py\n+++ b/file1.py\n@@ -1,3 +1,5 @@\n+# New comment\n def hello():\n-    print(\"Hello\")\n+    print(\"Hello World\")\n"
}
```

#### API 文档

启动服务后可访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## GitHub Token 获取

1. 登录 GitHub
2. 进入 Settings → Developer settings → Personal access tokens
3. 生成新 token，勾选 `repo` 权限（私有仓库需要）
4. 复制生成的 token

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

## 许可证

MIT License
