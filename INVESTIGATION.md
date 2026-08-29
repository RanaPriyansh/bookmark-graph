# Performance Investigation

## Identified Bottlenecks

### 1. CRITICAL: N+1 Query Problem in `_row_to_post()` (storage.py)
**Impact:** Every post retrieval makes 3 separate queries
- Line 256-260: SELECT mentions
- Line 263-266: SELECT hashtags  
- Line 269-272: SELECT urls

**Effect on operations:**
- `get_all_posts()` with N posts: 1 + 3N queries
- `search_posts()` with M results: 1 + 3M queries
- This is the **hottest bottleneck** - affects every read operation

### 2. HIGH: N+1 Insert Problem in `insert_posts()` (storage.py:79-119)
**Impact:** Individual INSERT for every relationship
- Each post: 1 INSERT + 3 DELETEs + (M mentions + H hashtags + U urls) individual INSERTs
- No batching with `executemany()`
- Transaction per post due to loop inside `with self.conn:`

### 3. HIGH: O(n²) in `build_adjacency_list()` (graph.py:36-40)
**Impact:** Nested loop comparing every mention against every post
```python
for post in posts:  # N posts
    for mention in post.mentions:  # M mentions
        for other_post in posts:  # N posts again!
```
This is O(N² × M) complexity

### 4. MEDIUM: Missing Indexes
- No index on `mentions.username` (used in get_neighbors)
- No index on `hashtags.tag` (used in stats queries)
- `posts.text` uses LIKE %...% causing full table scans

### 5. SECURITY: Path Traversal in CLI
- `--db` parameter accepts arbitrary paths without validation
- Could write to system directories

### 6. Missing CI
- No GitHub Actions workflow
- No automated test execution

## Fix Plan

1. Fix N+1 query with JOINs or bulk fetching
2. Fix N+1 insert with executemany() and proper transactions
3. Add indexes for common lookup patterns
4. Add path validation to CLI
5. Add GitHub Actions CI
6. Benchmark before/after on fixture + synthetic data
