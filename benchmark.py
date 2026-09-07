#!/usr/bin/env python3
"""Benchmark script to measure ingestion and query performance."""

import sys
import time
import tempfile
from pathlib import Path
from bookmark_graph.parser import parse_file
from bookmark_graph.storage import Storage
from bookmark_graph.models import Post


def generate_synthetic_data(output_path: Path, num_posts: int = 1000):
    """Generate synthetic JSONL data for benchmarking."""
    import json
    
    with open(output_path, 'w') as f:
        for i in range(num_posts):
            post = {
                'id': str(10000 + i),
                'text': f'Synthetic post {i} with some content #test{i % 10} #benchmark',
                'author': f'user{i % 50}',  # 50 distinct authors
                'created_at': f'2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z',
                'mentions': [f'user{(i + j) % 50}' for j in range(i % 3)],
                'hashtags': [f'test{i % 10}', 'benchmark'],
                'urls': [f'https://example.com/{i}'] if i % 5 == 0 else [],
                'reply_to': str(10000 + i - 1) if i > 0 and i % 10 == 0 else None,
            }
            f.write(json.dumps(post) + '\n')


def benchmark_ingest(db_path: Path, data_path: Path):
    """Benchmark the ingestion process."""
    print(f"\n=== Ingesting {data_path.name} ===")
    
    # Parse
    start = time.time()
    posts = parse_file(data_path)
    parse_time = time.time() - start
    print(f"Parse: {parse_time:.3f}s for {len(posts)} posts")
    
    # Insert
    storage = Storage(db_path)
    start = time.time()
    storage.insert_posts(posts)
    insert_time = time.time() - start
    print(f"Insert: {insert_time:.3f}s ({len(posts)/insert_time:.1f} posts/sec)")
    storage.close()
    
    return {
        'posts': len(posts),
        'parse_time': parse_time,
        'insert_time': insert_time,
    }


def benchmark_queries(db_path: Path):
    """Benchmark query operations."""
    print("\n=== Query Benchmarks ===")
    storage = Storage(db_path)
    
    # get_all_posts
    start = time.time()
    posts = storage.get_all_posts()
    get_all_time = time.time() - start
    print(f"get_all_posts(): {get_all_time:.3f}s for {len(posts)} posts ({len(posts)/get_all_time:.1f} posts/sec)")
    
    # search_posts
    start = time.time()
    results = storage.search_posts('test')
    search_time = time.time() - start
    print(f"search_posts('test'): {search_time:.3f}s ({len(results)} results)")
    
    # get_stats
    start = time.time()
    stats = storage.get_stats()
    stats_time = time.time() - start
    print(f"get_stats(): {stats_time:.3f}s")
    
    # get_neighbors (sample a few posts)
    neighbor_times = []
    for post in posts[:10]:
        start = time.time()
        neighbors = storage.get_neighbors(post.id)
        neighbor_times.append(time.time() - start)
    avg_neighbor_time = sum(neighbor_times) / len(neighbor_times)
    print(f"get_neighbors() avg: {avg_neighbor_time:.3f}s (10 samples)")
    
    storage.close()
    
    return {
        'get_all_time': get_all_time,
        'search_time': search_time,
        'stats_time': stats_time,
        'avg_neighbor_time': avg_neighbor_time,
    }


def main():
    fixture_path = Path('tests/fixtures/bookmarks.md')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test with fixture
        print("=" * 60)
        print("FIXTURE BENCHMARK (40 posts)")
        print("=" * 60)
        db_path = tmpdir / 'fixture.db'
        ingest_results = benchmark_ingest(db_path, fixture_path)
        query_results = benchmark_queries(db_path)
        
        # Test with synthetic larger dataset
        print("\n" + "=" * 60)
        print("SYNTHETIC BENCHMARK (1000 posts)")
        print("=" * 60)
        synthetic_path = tmpdir / 'synthetic.jsonl'
        generate_synthetic_data(synthetic_path, 1000)
        db_path_large = tmpdir / 'synthetic.db'
        ingest_results_large = benchmark_ingest(db_path_large, synthetic_path)
        query_results_large = benchmark_queries(db_path_large)
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Fixture (40 posts):")
        print(f"  Total ingest: {ingest_results['insert_time']:.3f}s")
        print(f"  get_all_posts: {query_results['get_all_time']:.3f}s")
        
        print(f"\nSynthetic (1000 posts):")
        print(f"  Total ingest: {ingest_results_large['insert_time']:.3f}s")
        print(f"  get_all_posts: {query_results_large['get_all_time']:.3f}s")
        print(f"  Throughput: {ingest_results_large['posts']/ingest_results_large['insert_time']:.1f} posts/sec")


if __name__ == '__main__':
    main()
