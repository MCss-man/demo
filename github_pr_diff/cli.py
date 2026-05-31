import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .github_client import GitHubClient
from .llm_analyzer import LLMAnalyzer
import json

app = typer.Typer()
console = Console()


def print_statistics(stats: dict):
    table = Table(title="Diff 统计信息", show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan")
    table.add_column("数量", style="green")
    table.add_row("文件变更", str(stats.get("files_changed", 0)))
    table.add_row("新增行数", str(stats.get("lines_added", 0)))
    table.add_row("删除行数", str(stats.get("lines_removed", 0)))
    table.add_row("总变更", str(stats.get("total_changes", 0)))
    console.print(table)


def print_summary(summary: dict):
    if not summary or "error" in summary:
        console.print("[yellow]无法获取摘要信息[/yellow]")
        return

    console.print("\n")
    console.print(Panel(summary.get("title", "无标题"), title="PR 标题", style="bold cyan"))
    console.print(f"\n[bold]文件变更:[/bold] {summary.get('files_changed', 'N/A')}")
    console.print(f"\n[bold]变更摘要:[/bold]")
    console.print(summary.get("changes_summary", "无"))

    key_changes = summary.get("key_changes", [])
    if key_changes:
        console.print(f"\n[bold]关键变更:[/bold]")
        for change in key_changes:
            console.print(f"  • {change}")

    console.print(f"\n[bold]风险评估:[/bold]")
    console.print(summary.get("risk_assessment", "无"))
    console.print(f"\n[bold]总体建议:[/bold]")
    console.print(summary.get("overall_suggestion", "无"))


def print_risks(risks_result: dict, min_confidence: str = "low"):
    risks = risks_result.get("risks", [])
    if not risks:
        console.print("[green]未发现风险[/green]")
        return

    confidence_order = {"low": 0, "medium": 1, "high": 2}
    min_level = confidence_order.get(min_confidence.lower(), 0)

    filtered_risks = []
    for risk in risks:
        risk_level = confidence_order.get(risk.get("confidence", "").lower(), 0)
        if risk_level >= min_level:
            filtered_risks.append(risk)

    if not filtered_risks:
        console.print("[green]没有符合最低置信度要求的风险[/green]")
        return

    table = Table(title=f"风险检测结果 ({len(filtered_risks)} 项)", show_header=True, header_style="bold red")
    table.add_column("严重程度", style="cyan", width=10)
    table.add_column("风险类型", style="magenta", width=20)
    table.add_column("描述", style="white")
    table.add_column("置信度", style="yellow", width=10)

    for risk in filtered_risks:
        confidence = risk.get("confidence", "low").lower()
        if confidence == "high":
            severity = "[red]高[/red]"
        elif confidence == "medium":
            severity = "[yellow]中[/yellow]"
        else:
            severity = "[blue]低[/blue]"

        table.add_row(
            severity,
            risk.get("type", "未知"),
            risk.get("description", "无描述"),
            risk.get("confidence", "low")
        )

    console.print(table)

    summary = risks_result.get("summary", "")
    if summary:
        console.print(f"\n[bold]风险总结:[/bold]\n{summary}")


def print_review(review_result: dict, risk_only: bool = False, min_confidence: str = "low"):
    if not review_result or "error" in review_result:
        console.print("[yellow]无法获取评审结果[/yellow]")
        return

    console.print("\n")
    console.print(Panel("[bold]完整代码评审报告[/bold]", style="bold green"))

    if "statistics" in review_result:
        print_statistics(review_result["statistics"])

    if not risk_only and "summary" in review_result:
        print_summary(review_result["summary"])

    if "risks" in review_result:
        print_risks(review_result["risks"], min_confidence)

    if not risk_only and "context" in review_result:
        context = review_result["context"]
        if context and "error" not in context:
            console.print(f"\n[bold]上下文分析:[/bold]")
            console.print(context.get("analysis", "无"))


@app.command()
def diff(
    owner: str = typer.Argument(..., help="GitHub repository owner"),
    repo: str = typer.Argument(..., help="GitHub repository name"),
    pr_number: int = typer.Argument(..., help="Pull Request number"),
    token: str = typer.Option(None, "--token", "-t", help="GitHub personal access token"),
    skip_ssl: bool = typer.Option(False, "--skip-ssl", help="Skip SSL certificate verification"),
    analyze: bool = typer.Option(False, "--analyze", "-a", help="Use LLM to analyze the diff"),
    llm_key: str = typer.Option(None, "--llm-key", help="LLM API key"),
    output: str = typer.Option("text", "--output", "-o", help="Output format: text/json"),
    risk_only: bool = typer.Option(False, "--risk-only", "-r", help="Only output risk detection results"),
    min_confidence: str = typer.Option("low", "--min-confidence", "-c", help="Minimum confidence threshold: low/medium/high"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache, force re-analysis"),
):
    client = GitHubClient(token=token, verify_ssl=not skip_ssl)
    try:
        diff_text = client.get_pr_diff_sync(owner, repo, pr_number)

        if not analyze:
            print(diff_text)
            return

        analyzer = LLMAnalyzer(api_key=llm_key)
        if not analyzer.available:
            console.print("[yellow]警告: LLM 分析不可用，请确保已安装 openai 依赖[/yellow]")
            return

        if risk_only:
            risks_result = analyzer.analyze_risks(diff_text, min_confidence=min_confidence)
            if risks_result.get("risks"):
                verified_risks = analyzer.verify_and_filter_risks(risks_result["risks"], diff_text)
                risks_result["risks"] = verified_risks

            if output == "json":
                result = {
                    "risks": risks_result.get("risks", []),
                    "summary": risks_result.get("summary", ""),
                    "statistics": analyzer.get_diff_statistics(diff_text)
                }
                console.print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_risks(risks_result, min_confidence)
        else:
            review_result = analyzer.analyze_full_review(diff_text, min_confidence=min_confidence)

            if output == "json":
                result = {
                    "statistics": review_result.get("statistics"),
                    "summary": review_result.get("summary"),
                    "risks": review_result.get("risks"),
                    "context": review_result.get("context")
                }
                console.print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_review(review_result, risk_only=False, min_confidence=min_confidence)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
