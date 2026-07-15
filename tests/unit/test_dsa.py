"""Tests for DSA algorithms in stats.py."""
import pytest
from backend.stats import (
    bfs_lineage,
    dfs_lineage,
    topological_sort,
    has_cycle,
    shortest_path_bfs,
    connected_components,
    binary_search_cdf,
    ks_test_binary,
    UnionFind,
    Trie,
    TrieNode,
    top_k_with_heap,
)


class TestBFSLineage:
    def test_bfs_single_node(self):
        graph = {"A": []}
        result = bfs_lineage("A", graph)
        assert result["nodes"] == ["A"]
        assert result["depths"] == {"A": 0}

    def test_bfs_linear_chain(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["D"]}
        result = bfs_lineage("A", graph)
        assert result["nodes"] == ["A", "B", "C", "D"]
        assert result["depths"]["D"] == 3

    def test_bfs_diamond(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        result = bfs_lineage("A", graph)
        assert "D" in result["nodes"]
        assert len(result["edges"]) == 4  # A->B, A->C, B->D, C->D

    def test_bfs_max_depth(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["D"], "D": ["E"]}
        result = bfs_lineage("A", graph, max_depth=2)
        assert "E" not in result["nodes"]

    def test_bfs_cycle_safety(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        result = bfs_lineage("A", graph)
        assert len(result["nodes"]) == 3  # No infinite loop


class TestDFSLineage:
    def test_dfs_linear_chain(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["D"]}
        result = dfs_lineage("A", graph)
        assert result["nodes"] == ["A", "B", "C", "D"]

    def test_dfs_topological_order(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        result = dfs_lineage("A", graph)
        # A should come before B and C
        assert result["topological_order"].index("A") < result["topological_order"].index("B")
        assert result["topological_order"].index("A") < result["topological_order"].index("C")


class TestTopologicalSort:
    def test_linear_chain(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["D"]}
        order = topological_sort(graph)
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_diamond(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        order = topological_sort(graph)
        assert order.index("A") < order.index("B")
        assert order.index("A") < order.index("C")
        assert order.index("B") < order.index("D")

    def test_cycle_raises(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        with pytest.raises(ValueError, match="Cycle detected"):
            topological_sort(graph)


class TestCycleDetection:
    def test_no_cycle(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        assert has_cycle(graph) is False

    def test_cycle_exists(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        assert has_cycle(graph) is True

    def test_self_loop(self):
        graph = {"A": ["A"]}
        assert has_cycle(graph) is True


class TestShortestPath:
    def test_direct_path(self):
        graph = {"A": ["B"], "B": ["C"]}
        path = shortest_path_bfs("A", "C", graph)
        assert path == ["A", "B", "C"]

    def test_no_path(self):
        graph = {"A": ["B"], "C": ["D"]}
        path = shortest_path_bfs("A", "D", graph)
        assert path is None

    def test_same_node(self):
        graph = {"A": ["B"]}
        path = shortest_path_bfs("A", "A", graph)
        assert path == ["A"]


class TestConnectedComponents:
    def test_single_component(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        components = connected_components(graph)
        assert len(components) == 1

    def test_multiple_components(self):
        graph = {"A": ["B"], "B": [], "C": ["D"], "D": []}
        components = connected_components(graph)
        assert len(components) == 2

    def test_isolated_node(self):
        graph = {"A": [], "B": ["C"], "C": []}
        components = connected_components(graph)
        assert len(components) == 2


class TestBinarySearchCDF:
    def test_empty_array(self):
        assert binary_search_cdf([], 5.0) == 0.0

    def test_all_less(self):
        assert binary_search_cdf([1, 2, 3], 5.0) == 1.0

    def test_all_greater(self):
        assert binary_search_cdf([4, 5, 6], 3.0) == 0.0

    def test_partial(self):
        assert binary_search_cdf([1, 2, 3, 4, 5], 3.0) == 0.6


class TestKSTestBinary:
    def test_identical_distributions(self):
        ref = [1, 2, 3, 4, 5]
        cur = [1, 2, 3, 4, 5]
        result = ks_test_binary(ref, cur)
        assert result.drifted is False
        assert result.value == 0.0

    def test_shifted_distribution(self):
        ref = [1, 2, 3, 4, 5]
        cur = [6, 7, 8, 9, 10]
        result = ks_test_binary(ref, cur)
        assert result.drifted is True

    def test_empty_data(self):
        result = ks_test_binary([], [1, 2, 3])
        assert result.drifted is False


class TestUnionFind:
    def test_basic_union(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("C", "D")
        assert uf.connected("A", "B") is True
        assert uf.connected("A", "C") is False

    def test_transitive_union(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        assert uf.connected("A", "C") is True

    def test_get_component(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        component = uf.get_component("A")
        assert set(component) == {"A", "B", "C"}

    def test_path_compression(self):
        uf = UnionFind()
        uf.union("A", "B")
        uf.union("B", "C")
        uf.union("C", "D")
        # After path compression, find should be fast
        assert uf.find("A") == uf.find("D")


class TestTrie:
    def test_insert_and_search(self):
        trie = Trie()
        trie.insert("churn_model", "urn:li:mlModel:churn")
        assert trie.search("churn_model") is True
        assert trie.search("churn") is False

    def test_prefix_search(self):
        trie = Trie()
        trie.insert("churn_model_v1", "urn:li:mlModel:v1")
        trie.insert("churn_model_v2", "urn:li:mlModel:v2")
        trie.insert("ltv_model", "urn:li:mlModel:ltv")
        results = trie.starts_with("churn")
        assert len(results) == 2

    def test_autocomplete(self):
        trie = Trie()
        for i in range(20):
            trie.insert(f"model_{i}", f"urn:model_{i}")
        results = trie.autocomplete("model", max_results=5)
        assert len(results) == 5

    def test_metadata(self):
        trie = Trie()
        trie.insert("test", "urn:test", {"type": "mlModel"})
        results = trie.search_prefix("test")
        assert len(results) == 1
        assert results[0][1]["type"] == "mlModel"


class TestTopKHeap:
    def test_basic(self):
        items = [5, 3, 8, 1, 9, 2]
        result = top_k_with_heap(items, 3)
        assert result == [9, 8, 5]

    def test_with_key_func(self):
        items = [{"score": 5}, {"score": 1}, {"score": 9}]
        result = top_k_with_heap(items, 2, key_func=lambda x: x["score"])
        assert result == [{"score": 9}, {"score": 5}]

    def test_k_larger_than_items(self):
        items = [1, 2, 3]
        result = top_k_with_heap(items, 10)
        assert result == [3, 2, 1]
