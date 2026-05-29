import typer
from .github_client import GitHubClient
from .llm_analyzer import LLMAnalyzer

app = typer.Typer()


@app.command()
def diff(
    owner: str = typer.Argument(..., help="GitHub repository owner"),
    repo: str = typer.Argument(..., help="GitHub repository name"),
    pr_number: int = typer.Argument(..., help="Pull Request number"),
    token: str = typer.Option(None, help="GitHub personal access token"),
    skip_ssl: bool = typer.Option(False, "--skip-ssl", help="Skip SSL certificate verification"),
    analyze: bool = typer.Option(False, "--analyze", help="Use LLM to analyze the diff"),
    llm_key: str = typer.Option(None, "--llm-key", help="LLM API key"),
):
    client = GitHubClient(token=token, verify_ssl=not skip_ssl)
    try:
        diff_text = client.get_pr_diff_sync(owner, repo, pr_number)
        print(diff_text)
        
        if analyze:
            typer.echo("\n" + "="*80)
            typer.echo("LLM 代码分析结果")
            typer.echo("="*80)
            
            analyzer = LLMAnalyzer(api_key=llm_key)
            if not analyzer.available:
                typer.echo("警告: LLM 分析不可用，请确保已安装 openai 依赖")
                return
            
            results = analyzer.analyze_pr_diff(diff_text)
            if results:
                for idx, result in enumerate(results, 1):
                    typer.echo(f"\n文件 {idx}: {result['filename']}")
                    typer.echo(f"  总结: {result['summary']}")
                    typer.echo(f"  建议:")
                    for i, suggestion in enumerate(result['suggestions'], 1):
                        typer.echo(f"    {i}. {suggestion}")
            else:
                typer.echo("未获取到分析结果")
                
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
