"""
Command Line Interface for Multi-Agent Blog Generator
"""

import click
import json
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from src.agents.orchestrator import MultiAgentOrchestrator
from src.config import get_settings, validate_configuration


console = Console()


@click.group()
def cli():
    """Multi-Agent Blog Generator CLI"""
    pass


@cli.command()
@click.option("--topic", "-t", required=True, help="Blog topic")
@click.option("--requirements", "-r", help="Additional requirements")
@click.option("--audience", "-a", default="general", help="Target audience")
@click.option("--tone", default="professional", help="Writing tone")
@click.option("--words", "-w", type=int, default=500, help="Target word count")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def generate(topic, requirements, audience, tone, words, output, format, verbose):
    """Generate a blog post"""
    
    # Setup logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Validate configuration
    console.print("[yellow]Validating configuration...[/yellow]")
    is_valid, error = validate_configuration()
    if not is_valid:
        console.print(f"[red]Configuration error: {error}[/red]")
        return
    
    console.print(Panel.fit(
        f"[bold]Topic:[/bold] {topic}\n"
        f"[bold]Audience:[/bold] {audience}\n"
        f"[bold]Tone:[/bold] {tone}\n"
        f"[bold]Target Words:[/bold] {words}",
        title="Blog Generation Settings"
    ))
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Run with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Generating blog post...", total=None)
        
        try:
            result = orchestrator.run(
                topic=topic,
                user_requirements=requirements,
                target_audience=audience,
                tone=tone,
                word_count=words
            )
            progress.update(task, completed=True)
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if verbose:
                console.print_exception()
            return
    
    # Display results
    _display_results(result, format, output)


@cli.command()
def check():
    """Check system configuration and dependencies"""
    
    console.print("[bold]Checking Multi-Agent Blog Generator...[/bold]\n")
    
    # Check configuration
    console.print("[cyan]Configuration:[/cyan]")
    is_valid, error = validate_configuration()
    if is_valid:
        console.print("  ✓ Configuration valid")
    else:
        console.print(f"  ✗ Configuration error: {error}")
    
    # Check settings
    settings = get_settings()
    console.print(f"  - LLM Provider: {settings.llm_provider}")
    console.print(f"  - LLM Model: {settings.llm_model}")
    console.print(f"  - Search Provider: {settings.search_provider}")
    
    # Check dependencies
    console.print("\n[cyan]Dependencies:[/cyan]")
    
    deps = [
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("duckduckgo_search", "DuckDuckGo Search"),
        ("fastapi", "FastAPI"),
        ("rich", "Rich"),
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            console.print(f"  ✓ {name}")
        except ImportError:
            console.print(f"  ✗ {name} not installed")
    
    # Check Ollama connection if using ollama
    if settings.llm_provider == "ollama":
        console.print("\n[cyan]Ollama Connection:[/cyan]")
        try:
            import requests
            response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                console.print(f"  ✓ Connected to Ollama")
                console.print(f"  - Available models: {len(models)}")
                
                # Check if configured model exists
                model_names = [m.get("name", "").split(":")[0] for m in models]
                if settings.llm_model in model_names:
                    console.print(f"  ✓ Model '{settings.llm_model}' available")
                else:
                    console.print(f"  ✗ Model '{settings.llm_model}' not found")
                    console.print(f"    Available: {', '.join(model_names)}")
            else:
                console.print(f"  ✗ Ollama returned status {response.status_code}")
        except Exception as e:
            console.print(f"  ✗ Cannot connect to Ollama: {str(e)}")
    
    console.print("\n[green]Check complete![/green]")


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def batch(config_file):
    """Generate multiple blog posts from a config file"""
    
    console.print(f"[yellow]Loading batch configuration from {config_file}...[/yellow]")
    
    # Load config
    with open(config_file, "r") as f:
        config = json.load(f)
    
    topics = config.get("topics", [])
    
    if not topics:
        console.print("[red]No topics found in configuration[/red]")
        return
    
    console.print(f"[green]Found {len(topics)} topics to process[/green]\n")
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Process each topic
    for idx, topic_config in enumerate(topics, 1):
        console.print(f"\n[bold cyan]Processing {idx}/{len(topics)}[/bold cyan]")
        
        try:
            result = orchestrator.run(
                topic=topic_config["topic"],
                user_requirements=topic_config.get("requirements"),
                target_audience=topic_config.get("audience", "general"),
                tone=topic_config.get("tone", "professional"),
                word_count=topic_config.get("word_count", 500)
            )
            
            # Save output
            output_file = topic_config.get("output", f"output_{idx}.md")
            _save_output(result, output_file, "markdown")
            
            console.print(f"[green]✓ Saved to {output_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Error: {str(e)}[/red]")
    
    console.print("\n[bold green]Batch processing complete![/bold green]")


def _display_results(result: dict, format: str, output_path: str = None):
    """Display or save results"""
    
    blog_post = result.get("blog_post", "")
    blog_title = result.get("blog_title", "Untitled")
    metadata = result.get("blog_metadata", {})
    quality_score = result.get("quality_score")
    
    # Format output
    if format == "markdown":
        content = f"# {blog_title}\n\n{blog_post}\n\n---\n"
        content += f"*Word Count: {metadata.get('word_count', 0)}*\n"
        if quality_score:
            content += f"*Quality Score: {quality_score:.2f}*\n"
    
    elif format == "json":
        content = json.dumps(result, indent=2, default=str)
    
    else:  # text
        content = f"{blog_title}\n\n{blog_post}"
    
    # Output
    if output_path:
        _save_output(result, output_path, format)
        console.print(f"\n[green]✓ Saved to {output_path}[/green]")
    else:
        console.print("\n" + "="*80 + "\n")
        if format == "markdown":
            console.print(Markdown(content))
        else:
            console.print(content)
        console.print("\n" + "="*80 + "\n")
    
    # Display metadata
    if metadata:
        console.print(Panel(
            f"[bold]Word Count:[/bold] {metadata.get('word_count', 0)}\n"
            f"[bold]Paragraphs:[/bold] {metadata.get('paragraph_count', 0)}\n"
            f"[bold]Reading Time:[/bold] {metadata.get('estimated_reading_time', 0)} min"
            + (f"\n[bold]Quality Score:[/bold] {quality_score:.2f}" if quality_score else ""),
            title="📊 Metadata"
        ))


def _save_output(result: dict, filepath: str, format: str):
    """Save output to file"""
    
    blog_post = result.get("blog_post", "")
    blog_title = result.get("blog_title", "Untitled")
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w") as f:
        if format == "markdown":
            f.write(f"# {blog_title}\n\n{blog_post}\n")
        elif format == "json":
            json.dump(result, f, indent=2, default=str)
        else:
            f.write(f"{blog_title}\n\n{blog_post}")


if __name__ == "__main__":
    cli()
