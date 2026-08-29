#!/usr/bin/env python3
"""Performance comparison benchmark for demonstrating optimizations."""

import sys
import time
import tempfile
from pathlib import Path
import json


def generate_synthetic_data(output_path: Path, num_posts: int = 10000):
    """Generate synthetic JSONL data for benchmarking."""
    with open(output_path, 'w') as f:
        for i in range(num_posts):
            post = {
                'id': str(100000 + i),
                'text': f'Synthetic post {i} with some content #test{i % 10} #benchmark',
                'author': f'user{i % 100}',  # 100 distinct authors
                'created_at': f'2024-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z',
                'mentions': [f'user{(i + j) % 100}' for j in range(min(i % 5, 3))],
                'hashtags': [f'test{i % 10}', 'benchmark'],
                'urls': [f'https://example.com/{i}'] if i % 5 == 0 else [],
                'reply_to': str(100000 + i - 1) if i > 0 and i % 10 == 0 else None,
            }
            f.write(json.dumps(post) + '\n')


def run_benchmark(num_posts):
    """Run benchmark with specified number of posts."""
    from bookmark_graph.parser import parse_file
    from bookmark_graph.storage import Storage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Generate data
        data_path = tmpdir / f'benchmark_{num_posts}.jsonl'
        generate_synthetic_data(data_path, num_posts)
        
        # Parse
        start = time.time()
        posts = parse_file(data_path)
        parse_time = time.time() - start
        
        # Insert
        db_path = tmpdir / 'benchmark.db'
        storage = Storage(db_path)
        start = time.time()
        storage.insert_posts(posts)
        insert_time = time.time() - start
        
        # Read all
        start = time.time()
        all_posts = storage.get_all_posts()
        read_time = time.time() - start
        
        storage.close()
        
        return {
            'posts': num_posts,
            'parse_time': parse_time,
            'insert_time': insert_time,
            'read_time': read_time,
        }


def main():
    print("=" * 70)
    print("SCALABILITY BENCHMARK")
    print("=" * 70)
    print("\nDemonstrating performance at scale with optimizations:")
    print("- Bulk inserts with executemany()")
    print("- Bulk relationship fetching (3 queries instead of 3N)")
    print("- Proper indexes on foreign keys")
    print()
    
    sizes = [100, 1000, 5000, 10000]
    
    results = []
    for size in sizes:
        print(f"Testing with {size:,} posts...")
        result = run_benchmark(size)
        results.append(result)
        print(f"  Insert: {result['insert_time']:.3f}s ({result['posts']/result['insert_time']:.0f} posts/sec)")
        print(f"  Read:   {result['read_time']:.3f}s ({result['posts']/result['read_time']:.0f} posts/sec)")
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Posts':<10} {'Insert (s)':<12} {'Read (s)':<12} {'Insert Rate':<15} {'Read Rate'}")
    print("-" * 70)
    for r in results:
        print(f"{r['posts']:<10} {r['insert_time']:<12.3f} {r['read_time']:<12.3f} "
              f"{r['posts']/r['insert_time']:<15.0f} {r['posts']/r['read_time']:.0f}")


if __name__ == '__main__':
    main()
