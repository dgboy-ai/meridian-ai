"""Verify all DSA algorithms work correctly."""
from backend.stats import (
    bfs_lineage, dfs_lineage, topological_sort, has_cycle,
    shortest_path_bfs, connected_components, binary_search_cdf,
    ks_test_binary, UnionFind, Trie, top_k_with_heap
)

print("=== DSA VERIFICATION ===")

# 1. BFS
g = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
r = bfs_lineage("A", g)
assert len(r["nodes"]) == 4, f"BFS nodes: {len(r['nodes'])}"
assert len(r["edges"]) == 4, f"BFS edges: {len(r['edges'])}"
print("OK: BFS lineage traversal")

# 2. DFS
r = dfs_lineage("A", g)
assert len(r["nodes"]) == 4
print("OK: DFS lineage traversal")

# 3. Topological Sort
order = topological_sort(g)
assert order.index("A") < order.index("D")
print("OK: Topological sort")

# 4. Cycle Detection
assert has_cycle(g) == False
assert has_cycle({"A": ["B"], "B": ["C"], "C": ["A"]}) == True
print("OK: Cycle detection")

# 5. Shortest Path
path = shortest_path_bfs("A", "D", g)
assert path == ["A", "B", "D"] or path == ["A", "C", "D"]
print("OK: Shortest path BFS")

# 6. Connected Components
comps = connected_components(g)
assert len(comps) == 1
print("OK: Connected components")

# 7. Binary Search CDF
assert binary_search_cdf([1, 2, 3, 4, 5], 3) == 0.6
print("OK: Binary search CDF")

# 8. KS-Test Binary
r = ks_test_binary([1, 2, 3], [4, 5, 6])
assert r.drifted == True
print("OK: KS-test binary")

# 9. Union-Find
uf = UnionFind()
uf.union("A", "B")
uf.union("B", "C")
uf.union("D", "E")
assert uf.connected("A", "C") == True
assert uf.connected("A", "D") == False
print("OK: Union-Find")

# 10. Trie
t = Trie()
t.insert("churn_model", "urn:1")
t.insert("churn_v2", "urn:2")
t.insert("ltv_model", "urn:3")
results = t.starts_with("churn")
assert len(results) == 2
print("OK: Trie prefix search")

# 11. Top-K Heap
items = [5, 3, 8, 1, 9, 2]
top3 = top_k_with_heap(items, 3)
assert top3 == [9, 8, 5]
print("OK: Top-K heap")

print()
print("=== ALL 11 DSA ALGORITHMS VERIFIED ===")
