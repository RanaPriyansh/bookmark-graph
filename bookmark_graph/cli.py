"""Command-line interface for bookmark-graph."""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from .parser import parse_file, ParserError
from .storage import Storage
from .graph import Graph
from .export import Exporter


console = Console()


def validate_db_path(db_path: str) -> Path:
    """Validate database path to prevent path traversal attacks.
    
    Args:
        db_path: Database file path
        
    Returns:
        Validated Path object
        
    Raises:
        click.BadParameter: If path is invalid or unsafe
    """
    # Ensure the path doesn't contain suspicious patterns
    if '..' in db_path or db_path.startswith('/etc') or db_path.startswith('/sys'):
        raise click.BadParameter(
            f"Invalid database path: {db_path}. "
            "Path must not traverse directories or target system paths."
        )
    
    path = Path(db_path).resolve()
    
    return path


@click.group()
@click.version_option(version='0.1.0')
def main():
    """bookmark-graph: Turn X bookmark exports into knowledge graphs.
    
    A local CLI tool for analyzing and visualizing bookmarked posts.
    """
    pass


@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--db', default='bookmarks.db', help='Database file path')
def ingest(input_file, db):
    """Ingest bookmark export file (JSONL or Markdown)."""
    try:
        db_path = validate_db_path(db)
        
        console.print(f"[bold blue]Parsing {input_file}...[/bold blue]")
        posts = parse_file(Path(input_file))
        console.print(f"[green]✓[/green] Parsed {len(posts)} posts")
        
        console.print(f"[bold blue]Storing in {db}...[/bold blue]")
        storage = Storage(db_path)
        storage.insert_posts(posts)
        storage.close()
        
        console.print(f"[green]✓[/green] Successfully ingested {len(posts)} posts")
        
    except ParserError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except click.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.option('--db', default='bookmarks.db', help='Database file path')
def stats(db):
    """Show graph statistics."""
    try:
        db_path = validate_db_path(db)
        
        if not db_path.exists():
            console.print(f"[bold red]Error:[/bold red] Database not found: {db}")
            console.print("Run 'bookmark-graph ingest' first.")
            raise click.Abort()
        
        storage = Storage(db_path)
        graph = Graph(storage)
        stats = storage.get_stats()
        
        # Display stats in a table
        table = Table(title="Bookmark Graph Statistics", show_header=False)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Posts", str(stats.total_posts))
        table.add_row("Total Authors", str(stats.total_authors))
        table.add_row("Total Hashtags", str(stats.total_hashtags))
        table.add_row("Total Mentions", str(stats.total_mentions))
        table.add_row("Total URLs", str(stats.total_urls))
        table.add_row("Total Replies", str(stats.total_replies))
        
        console.print(table)
        
        # Show top authors
        console.print("\\n[bold]Top Authors:[/bold]")
        top_authors = graph.get_top_authors(10)
        for author, count in top_authors:
            console.print(f"  @{author}: {count} posts")
        
        # Show top hashtags
        console.print("\\n[bold]Top Hashtags:[/bold]")
        top_hashtags = graph.get_top_hashtags(10)
        for hashtag, count in top_hashtags:
            console.print(f"  #{hashtag}: {count} uses")
        
        storage.close()
        
    except click.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.argument('search_query')
@click.option('--db', default='bookmarks.db', help='Database file path')
@click.option('--limit', default=10, help='Maximum results to show')
def query(search_query, db, limit):
    """Search posts by text content."""
    try:
        db_path = validate_db_path(db)
        
        if not db_path.exists():
            console.print(f"[bold red]Error:[/bold red] Database not found: {db}")
            console.print("Run 'bookmark-graph ingest' first.")
            raise click.Abort()
        
        storage = Storage(db_path)
        posts = storage.search_posts(search_query)
        
        console.print(f"\\n[bold]Found {len(posts)} matching posts[/bold]")
        
        for i, post in enumerate(posts[:limit], 1):
            panel = Panel(
                f"[bold]@{post.author}[/bold]\\n"
                f"{post.text}\\n\\n"
                f"[dim]ID: {post.id} | Created: {post.created_at}[/dim]",
                title=f"Post {i}",
                border_style="blue"
            )
            console.print(panel)
        
        if len(posts) > limit:
            console.print(f"\\n[dim]... and {len(posts) - limit} more[/dim]")
        
        storage.close()
        
    except click.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.argument('post_id')
@click.option('--db', default='bookmarks.db', help='Database file path')
def neighbors(post_id, db):
    """Show neighboring posts (replies, mentions, same author)."""
    try:
        db_path = validate_db_path(db)
        
        if not db_path.exists():
            console.print(f"[bold red]Error:[/bold red] Database not found: {db}")
            console.print("Run 'bookmark-graph ingest' first.")
            raise click.Abort()
        
        storage = Storage(db_path)
        post = storage.get_post(post_id)
        
        if not post:
            console.print(f"[bold red]Error:[/bold red] Post not found: {post_id}")
            raise click.Abort()
        
        # Show original post
        console.print(Panel(
            f"[bold]@{post.author}[/bold]\\n{post.text}",
            title="Original Post",
            border_style="green"
        ))
        
        # Get neighbors
        neighbors = storage.get_neighbors(post_id)
        
        # Show replies
        if neighbors['replies']:
            console.print(f"\\n[bold cyan]Replies ({len(neighbors['replies'])}):[/bold cyan]")
            for reply in neighbors['replies'][:5]:
                console.print(f"  • @{reply.author}: {reply.text[:60]}...")
        
        # Show mentions
        if neighbors['mentioned_in']:
            console.print(f"\\n[bold cyan]Mentioned in ({len(neighbors['mentioned_in'])}):[/bold cyan]")
            for mention in neighbors['mentioned_in'][:5]:
                console.print(f"  • @{mention.author}: {mention.text[:60]}...")
        
        # Show same author
        if neighbors['by_same_author']:
            console.print(f"\\n[bold cyan]By same author ({len(neighbors['by_same_author'])}):[/bold cyan]")
            for same in neighbors['by_same_author'][:5]:
                console.print(f"  • {same.text[:60]}...")
        
        storage.close()
        
    except click.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@main.command()
@click.argument('output_file', type=click.Path())
@click.option('--db', default='bookmarks.db', help='Database file path')
@click.option('--format', type=click.Choice(['json', 'mermaid', 'graphviz'], case_sensitive=False),
              default='json', help='Export format')
@click.option('--max-nodes', default=50, help='Maximum nodes for diagram exports')
def export(output_file, db, format, max_nodes):
    """Export graph data (JSON, Mermaid, or Graphviz)."""
    try:
        db_path = validate_db_path(db)
        
        if not db_path.exists():
            console.print(f"[bold red]Error:[/bold red] Database not found: {db}")
            console.print("Run 'bookmark-graph ingest' first.")
            raise click.Abort()
        
        storage = Storage(db_path)
        exporter = Exporter(storage)
        output_path = Path(output_file)
        
        console.print(f"[bold blue]Exporting as {format}...[/bold blue]")
        
        if format == 'json':
            exporter.export_json(output_path)
        elif format == 'mermaid':
            exporter.export_mermaid(output_path, max_nodes=max_nodes)
        elif format == 'graphviz':
            exporter.export_graphviz(output_path, max_nodes=max_nodes)
        
        console.print(f"[green]✓[/green] Exported to {output_file}")
        
        storage.close()
        
    except click.BadParameter as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


if __name__ == '__main__':
    main()
