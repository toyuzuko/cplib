# cplib.graph

`cplib.graph` contains graph and tree algorithms.

Use `cplib.graph` as the common import entry point for graph and tree APIs. Direct imports from individual modules are also supported.

- `core`: graph and tree containers; `base`: shared types.
- `walk`: DFS, cycles, and walks; `reachability`: SCC, DAG order, reachability, and dominators.
- `lowlink`: undirected decompositions and compressed forests.
- `tree`: static tree algorithms; `treedecomp`: decompositions and LCA; `treequery`: queries; `treedp`: rerooting and fixed-root tree DP.
- `linkcut` and `eulertourtree`: dynamic forests; `toptree`: static and dynamic top-tree DP; `connectivity`: dynamic graph connectivity.

`TopTree` supports dynamic tree DP with a commutative rake monoid, without inverses. `RerootingLinkCutTree` is an alternative when inverses are available. All top-tree variants live in `toptree`:

| Payloads | Fixed topology and root | Dynamic forest |
| --- | --- | --- |
| Vertices | `StaticTopTree` | `TopTree` |
| Vertices and edges | `StaticTopTreeWithEdges` | `TopTreeWithEdges` |

The vertex variants share `point_identity`, `add_vertex(point, value)`, `add_edge(path)`, `rake`, `compress`, and `set`/`get`. The edge variants instead share `vertex_cluster(point, vertex_value)`, `edge_cluster(point, edge_value)`, and `set_vertex`/`get_vertex`/`set_edge`/`get_edge`. Both static constructors take a built `Tree`; the dynamic edge constructor takes endpoint pairs in edge-ID order. Dynamic edge slots are detached with `cut_edge(edge_id)` and reused with `link_edge(edge_id, child, parent)`.

Static `tree_value()` uses the fixed root; dynamic `tree_value(vertex)` changes the represented root. Subtree results exclude the incoming parent edge. Dynamic `path_cluster_value(u, v)` includes off-path branches. Callbacks must define a consistent DP across decompositions; only the static versions permit noncommutative rake with fixed light-child order.

```python
from cplib.graph import EulerTourTree, HeavyLightDecomposition, LinkCutTree, StaticTopTree, TopTree
```

## Modules

### `base.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |

### `connectivity.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `UndoableDSUWithComponentAggregate` | class | `UndoableDSUWithComponentAggregate(n: int, op: Callable[[ValueT, ValueT], ValueT], inv: Callable…` | Undoable Disjoint Set Union with component aggregate support. | Space: O(n + h) |
| `UndoableDSUWithLazyAggregate` | class | `UndoableDSUWithLazyAggregate(values: list[VertexValueT], op: Callable[[AggregateT, AggregateT],…` | Undoable DSU supporting vertex updates and component lazy updates. | Space: O(n + h) |
| `OfflineDynamicConnectivity` | class | `OfflineDynamicConnectivity(n: int, time_max: int, values: list[VertexValueT] \| None = None, op:…` | Offline dynamic connectivity with queries. | Space: O(n + time_max + q + k log time_max), where ``q`` is the number of stored point queries and ``k`` is the number of edge-active intervals |
| `SimpleOnlineDynamicConnectivity` | class | `SimpleOnlineDynamicConnectivity(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], valu…` | Simple online dynamic connectivity with component aggregates. | Space: O(n + m) |
| `HDLTOnlineDynamicConnectivity` | class | `HDLTOnlineDynamicConnectivity(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], values…` | HDLT-style online dynamic connectivity with component aggregates. | Space: O((n + m) log n) |

### `core.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Graph` | class | `Graph(n: int, is_directed: bool = False, connectivity_check: bool = False)` | Graph data structure for competitive programming. | Space: ``O(n + m)`` |
| `CSRGraph` | class | `CSRGraph(n: int, edges: Sequence[tuple[Node, Node] \| tuple[Node, Node, Weight]], is_directed: b…` | Static graph representation using Compressed Sparse Row layout. | Space: O(n + m) |
| `Tree` | class | `Tree(n: int, connectivity_check: bool = False)` | Rooted tree container with parent, depth, and subtree metadata. | Space: ``O(n)`` |

### `counting.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `chromatic_number` | function | `chromatic_number(graph: Graph) -> int` | Return the chromatic number of a simple undirected graph. | Time: ``O(n 2^n)`` |
| `chromatic_polynomial` | function | `chromatic_polynomial(graph: Graph, mod: int = 998244353) -> FormalPowerSeriesMod` | Return the chromatic polynomial coefficients modulo ``mod``. | Time: ``O(n^3 2^n)`` via subset-convolution-based power projection |
| `count_spanning_trees` | function | `count_spanning_trees(graph: Graph, mod: int = 998244353) -> int` | Alias for :func:`kirchhoff_theorem` to count spanning trees in an undirected graph. | Time: ``O(n^3)`` |
| `count_rooted_arborescences` | function | `count_rooted_arborescences(graph: Graph, root: Node, mod: int = 998244353) -> int` | Alias for :func:`kirchhoff_theorem` to count rooted arborescences in a directed graph. | Time: ``O(n^3)`` |
| `kirchhoff_theorem` | function | `kirchhoff_theorem(graph: Graph, root: Node \| None = None, mod: int = 998244353) -> int` | Count spanning trees using Kirchhoff's matrix-tree theorem. | Time: Dominated by determinant computation: typically ``O(n^3)`` |
| `induced_subgraph` | function | `induced_subgraph(graph: Graph, vertices: list[Node]) -> Graph` | Return the subgraph induced by a subset of vertices. | Time: ``O(\sum_{v \in S} \deg(v))``, where ``S`` is ``vertices`` |
| `count_eulerian_circuits` | function | `count_eulerian_circuits(graph: Graph, mod: int = 998244353) -> int` | Alias for :func:`best_theorem` to count Eulerian circuits in a directed graph. | Time: ``O(n^3 + m)`` |
| `best_theorem` | function | `best_theorem(graph: Graph, mod: int = 998244353) -> int` | Count Eulerian circuits in a directed graph using the BEST theorem. | Time: Dominated by Kirchhoff on the non-isolated subgraph: typically ``O(n^3)`` |

### `eulertourtree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `EulerTourTree` | class | `EulerTourTree(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT])` | Euler Tour Tree for dynamic forests with component aggregates. | Space: O(n) |

### `families.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FunctionalGraph` | class | `FunctionalGraph(to: Sequence[int], start_values: Sequence[ValueT] \| None = None, step_values: S…` | Functional graph with cycle decomposition and optional walk aggregation. | Space: O(n) |
| `Namori` | class | `Namori(graph: Graph)` | Connected undirected graph with exactly one simple cycle. | Space: O(n) |
| `Pseudotree` | class | `Pseudotree(graph: Graph)` | Undirected graph whose every connected component has at most one cycle. | Space: O(n) |
| `CactusGraph` | class | `CactusGraph(graph: Graph)` | Undirected cactus graph decomposition. | Space: O(n + m) |

### `flow.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `MaximumFlowEdge` | class | `MaximumFlowEdge(...)` | Edge information in maximum flow result. | Space: O(1) |
| `MaximumFlowResult` | class | `MaximumFlowResult(...)` | Result of maximum flow computation. | Space: O(m), where m is the number of reported edges |
| `MinimumCostBFlowEdge` | class | `MinimumCostBFlowEdge(...)` | Edge information in minimum cost b-flow result. | Space: O(1) |
| `MinimumCostBFlowResult` | class | `MinimumCostBFlowResult(...)` | Result of minimum cost b-flow computation. | Space: O(m), where m is the number of reported edges |
| `MaximumFlow` | class | `MaximumFlow(n: int)` | Maximum flow solver using Dinic's algorithm with current-edge optimization. | Space: O(n + m) |
| `BipartiteMatching` | class | `BipartiteMatching(n1: int, n2: int)` | Bipartite matching solver using maximum flow. | Space: O(n1 + n2 + m) |
| `MinimumCostBFlow` | class | `MinimumCostBFlow(n: int)` | Minimum cost b-flow solver using cost-scaling algorithm. | Space: O(n + m) |

### `grid.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `GridComponentsResult` | class | `GridComponentsResult(...)` | Connected components of passable cells in a grid. | Space: O(hw), where ``h`` and ``w`` are grid dimensions. |
| `grid_index` | function | `grid_index(row: int, col: int, width: int) -> int` | Convert a grid coordinate to a flat index. | Time: O(1) |
| `grid_position` | function | `grid_position(index: int, width: int) -> tuple[int, int]` | Convert a flat index to a grid coordinate. | Time: O(1) |
| `grid_neighbors4` | function | `grid_neighbors4(row: int, col: int, height: int, width: int) -> Iterator[tuple[int, int]]` | Iterate over 4-neighbor cells inside the grid. | Time: O(1) |
| `grid_neighbors8` | function | `grid_neighbors8(row: int, col: int, height: int, width: int) -> Iterator[tuple[int, int]]` | Iterate over 8-neighbor cells inside the grid. | Time: O(1) |
| `grid_bfs` | function | `grid_bfs(grid: Sequence[Sequence[CellT]], starts: Iterable[tuple[int, int]], passable: Callable…` | Return unweighted shortest distances on an implicit grid graph. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |
| `grid_connected_components` | function | `grid_connected_components(grid: Sequence[Sequence[CellT]], passable: Callable[[CellT], bool] \|…` | Compute connected components of passable cells in an implicit grid graph. | Time: O(hw), where ``h`` and ``w`` are grid dimensions. |

### `linkcut.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `LinkCutTree` | class | `LinkCutTree(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT])` | Link-cut tree for dynamic forests with orientation-insensitive path folds. | Space: O(n) |
| `BidirectionalLinkCutTree` | class | `BidirectionalLinkCutTree(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT])` | Link-cut tree for dynamic forests with orientation-aware path folds. | Space: O(n) |
| `LazyPathLinkCutTree` | class | `LazyPathLinkCutTree(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], mapping: Callabl…` | Link-cut tree with lazy path updates and path queries. | Space: O(n) |
| `LazySubtreeLinkCutTree` | class | `LazySubtreeLinkCutTree(n: int, e: ValueT, op: Callable[[ValueT, ValueT], ValueT], inv: Callable…` | Link-cut tree with lazy subtree updates and commutative aggregates. | Space: O(n) |
| `DynamicTreeAddTreeSum` | class | `DynamicTreeAddTreeSum(n: int)` | Dynamic tree for subtree-add and subtree-sum queries. | Space: O(n) |
| `RerootingLinkCutTree` | class | `RerootingLinkCutTree(values: Sequence[ValueT], point_identity: PointT, add_vertex: Callable[[Po…` | Link-cut tree for dynamic rerooting-style tree aggregation. | Space: O(n) |
| `RerootingLinkCutTreeWithEdges` | class | `RerootingLinkCutTreeWithEdges(n: int, point_identity: PointT, add_vertex: Callable[[PointT, Val…` | Rerooting link-cut forest with values on vertices and edges. | Space: O(n + m), for n original vertices and m registered edge slots. |

### `lowlink.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `LowLinkResult` | class | `LowLinkResult(...)` | Result of lowlink analysis on an undirected graph. | Space: ``O(n + b)``, where ``b`` is the number of bridges. |
| `LowLinkAnalysisResult` | class | `LowLinkAnalysisResult(...)` | Lowlink analysis including vertex-biconnected components. | Space: O(n + m) for n vertices and m edges. |
| `analyze_lowlink` | function | `analyze_lowlink(graph: Graph) -> LowLinkAnalysisResult` | Run lowlink analysis, including vertex-biconnected components. | Time: ``O(n + m)`` |
| `lowlink` | function | `lowlink(graph: Graph) -> LowLinkResult` | Compute lowlink information for an undirected graph. | Time: ``O(n + m)`` |
| `BlockCutTreeResult` | class | `BlockCutTreeResult(...)` | Result of block-cut forest construction. | Space: O(n + m), including component memberships and vertex mappings. |
| `BridgeTreeResult` | class | `BridgeTreeResult(...)` | Result of bridge-forest construction. | Space: O(n), including component memberships and the bridge forest. |
| `biconnected_components` | function | `biconnected_components(graph: Graph) -> list[list[Node]]` | Enumerate biconnected components as vertex sets. | Time: ``O(n + m)`` |
| `block_cut_tree` | function | `block_cut_tree(graph: Graph) -> BlockCutTreeResult` | Build the block-cut forest of an undirected graph. | Time: ``O(n + m)`` |
| `two_edge_connected_components` | function | `two_edge_connected_components(graph: Graph) -> list[list[Node]]` | Enumerate two-edge-connected components. | Time: ``O(n + m)`` |
| `bridge_tree` | function | `bridge_tree(graph: Graph) -> BridgeTreeResult` | Build the bridge forest of an undirected graph. | Time: ``O(n + m)`` |

### `matching.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `MatchingSuccess` | class | `MatchingSuccess(...)` | Successful matching result. | Space: O(k), where k is the number of matched edges. |
| `MatchingFailure` | class | `MatchingFailure(...)` | Failed matching result. | Space: O(1) |
| `MaximumWeightMatching` | class | `MaximumWeightMatching(n: int)` | General weighted matching algorithm for undirected graphs. | Space: O(n^2) |
| `MinimumWeightPerfectMatching` | class | `MinimumWeightPerfectMatching(n: int)` | Minimum‑weight **perfect** matching for general (non‑bipartite) graphs. | Space: O(n^2 + m) |
| `BipartiteMaximumMatching` | class | `BipartiteMaximumMatching(n1: int, n2: int)` | Maximum bipartite matching solver using augmenting path algorithm with DFS. | Space: O(n1 + n2 + m) |
| `BipartiteMinimumWeightMaximumMatching` | class | `BipartiteMinimumWeightMaximumMatching(n1: int, n2: int)` | Minimum weight maximum bipartite matching solver using the Hungarian algorithm. | Space: O(n1 n2) |
| `BipartiteMaximumWeightMatching` | class | `BipartiteMaximumWeightMatching(n1: int, n2: int)` | Maximum weight bipartite matching solver using Hungarian algorithm. | Space: O(n1 n2) |

### `optimization.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `maximum_independent_set` | function | `maximum_independent_set(graph: Graph) -> list[Node]` | Find one maximum independent set of a simple undirected graph. | Time: Exponential in ``n`` in the worst case. |
| `maximum_clique` | function | `maximum_clique(graph: Graph) -> list[Node]` | Find one maximum clique of a simple undirected graph. | Time: Exponential in ``n`` in the worst case. |
| `minimum_vertex_cover` | function | `minimum_vertex_cover(graph: Graph) -> list[Node]` | Find one minimum vertex cover of a simple undirected graph. | Time: Exponential in ``n`` in the worst case. |
| `bounded_vertex_cover` | function | `bounded_vertex_cover(graph: Graph, k: int) -> list[Node] \| None` | Find a vertex cover of size at most ``k`` by bounded search tree. | Time: O(2^k n m) in the worst case. |
| `MinimumSteinerTreeResult` | class | `MinimumSteinerTreeResult(...)` | Result of a minimum Steiner tree query. | Space: ``O(e)``, where ``e`` is the number of reported edges. |
| `minimum_steiner_tree` | function | `minimum_steiner_tree(graph: Graph, terminals: list[Node]) -> MinimumSteinerTreeResult` | Find the minimum Steiner tree connecting all terminal vertices. | Time: ``O(3^k n + 2^k m log n)``, where ``k = len(terminals)`` |
| `undirected_chinese_postman_problem` | function | `undirected_chinese_postman_problem(graph: Graph) -> Weight` | Return the shortest closed walk length that traverses every edge. | Time: O(n^3 + k^2 2^k), where ``k`` is the number of odd-degree vertices. |
| `bitonic_tsp` | function | `bitonic_tsp(points: list[tuple[float, float]]) -> float` | Return the length of a shortest bitonic tour through planar points. | Time: O(n^2), where ``n`` is ``len(points)``. |
| `TravelingSalesmanResult` | class | `TravelingSalesmanResult(...)` | Result of one traveling salesman query. | Space: ``O(n)`` |
| `traveling_salesman_problem` | function | `traveling_salesman_problem(graph: Graph) -> TravelingSalesmanResult` | Solve the traveling salesman problem starting and ending at vertex ``0``. | Time: ``O(m + n^2 2^n)`` |

### `reachability.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `NodeGroupingResult` | class | `NodeGroupingResult(...)` | Partition of vertices into groups. | Space: ``O(n)`` |
| `strongly_connected_components` | function | `strongly_connected_components(graph: Graph) -> NodeGroupingResult` | Compute strongly connected components of a directed graph. | Time: ``O(n + m)`` |
| `strongly_connected_components_raw_csr` | function | `strongly_connected_components_raw_csr(n: int, start: Sequence[int], to: Sequence[int]) -> NodeG…` | Compute strongly connected components from raw CSR arrays. | Time: O(n + m), where ``m = len(to)``. |
| `strongly_connected_components_csr` | function | `strongly_connected_components_csr(graph: CSRGraph) -> NodeGroupingResult` | Compute strongly connected components of a directed CSR graph. | Time: O(n + m) |
| `topological_sort` | function | `topological_sort(graph: Graph) -> list[Node]` | Return one topological order of a directed acyclic graph. | Time: ``O(n + m)`` |
| `OfflineDagReachability` | class | `OfflineDagReachability(graph: Graph, topological_order: Sequence[Node] \| None = None, block_siz…` | Offline reachability queries on a DAG. | Space: O(nB / w), where ``B`` is ``block_size`` and ``w`` is the machine word size used by Python integers. |
| `offline_reachability` | function | `offline_reachability(graph: Graph, queries: Sequence[tuple[Node, Node]], block_size: int = 4096…` | Offline reachability queries on a directed graph. | Time: O(n + m + ceil(q / B) * (c + e) * B / w + q), where ``c`` and ``e`` are the number of vertices and edges of the condensation DAG. |
| `dominator_tree` | function | `dominator_tree(graph: Graph, root: Node) -> list[Node]` | Compute immediate dominators from one root. | Time: Near-linear, typically ``O((n + m) alpha(n))`` |
| `complement_connected_components` | function | `complement_connected_components(graph: Graph) -> NodeGroupingResult` | Compute connected components of the complement of an undirected graph. | Time: O(n^2) in the size of the processed input or stored data |

### `scheduling.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `optimal_scheduling_on_tree` | function | `optimal_scheduling_on_tree(tree: Tree, proc_time: list[int], weight: list[int])` | Find an optimal scheduling order for jobs whose precedence constraints form a rooted tree. | Time: O(n^2) in the size of the processed input or stored data |
| `optimal_scheduling_on_dag` | function | `optimal_scheduling_on_dag(g: Graph, proc_time: list[int], weight: list[int]) -> tuple[int, list…` | Finds the optimal scheduling order for jobs on a DAG with precedence constraints. | Time: O(n^2 2^n) |

### `shortest.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `dijkstra_with_prev` | function | `dijkstra_with_prev(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]` | Run Dijkstra's algorithm and keep predecessor information. | Time: ``O((n + m) log n)`` |
| `radix_dijkstra_with_prev` | function | `radix_dijkstra_with_prev(graph: Graph, source: Node) -> tuple[list[Weight], list[Node]]` | Run Dijkstra's algorithm with a radix heap. | Time: O((n + m) log C), where ``C`` is the maximum shortest-path distance. |
| `simplify_graph` | function | `simplify_graph(graph: Graph) -> Graph` | Remove self-loops and merge parallel edges by minimum weight. | Time: ``O(n + m)`` |
| `dijkstra` | function | `dijkstra(graph: Graph, source: Node) -> list[Weight]` | Return shortest distances from ``source`` using Dijkstra's algorithm. | Time: O((n + m) log n) |
| `radix_dijkstra` | function | `radix_dijkstra(graph: Graph, source: Node) -> list[Weight]` | Return shortest distances from ``source`` using radix-heap Dijkstra. | Time: O((n + m) log C), where ``C`` is the maximum shortest-path distance. |
| `bfs` | function | `bfs(graph: Graph, source: Node) -> list[Weight]` | Return shortest distances from ``source`` in an unweighted graph. | Time: O(n + m) |
| `bellman_ford` | function | `bellman_ford(graph: Graph, source: Node) -> list[Weight]` | Return shortest distances from ``source`` using Bellman-Ford. | Time: O(n m) |
| `ShortestPathResult` | class | `ShortestPathResult(...)` | Result of shortest path computation. | Space: ``O(k)``, where ``k`` is the path length. |
| `shortest_path` | function | `shortest_path(graph: Graph, source: Node, target: Node) -> ShortestPathResult` | Return one shortest path from ``source`` to ``target``. | Time: Dominated by the selected single-source shortest-path algorithm; O(n + m) for BFS on unweighted graphs; O((n + m) log n) for Dijkstra on graphs with non-negative weights; O(n m) for Bellman-Ford on graphs with negative weights |
| `warshall_floyd` | function | `warshall_floyd(graph: Graph) -> list[list[Weight]]` | Return all-pairs shortest-path distances. | Time: O(n^3) |
| `update_dist_matrix` | function | `update_dist_matrix(dist_matrix: list[list[Weight]], u: Node, v: Node, w: Weight, is_directed: b…` | Update an all-pairs distance matrix after inserting one edge. | Time: O(n^2) in the size of the processed input or stored data |

### `spanning.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `MinimumSpanningTreeResult` | class | `MinimumSpanningTreeResult(...)` | Result of minimum spanning tree computation. | Space: O(n) |
| `minimum_spanning_tree` | function | `minimum_spanning_tree(graph: Graph) -> MinimumSpanningTreeResult` | Find the minimum spanning tree using Kruskal's algorithm. | Time: O(m log m) |
| `directed_minimum_spanning_tree` | function | `directed_minimum_spanning_tree(graph: Graph, root: Node) -> MinimumSpanningTreeResult` | Find the minimum spanning tree in a directed graph (minimum arborescence). | Time: O((n + m) log n) |
| `MinimumDiameterSpanningTreeResult` | class | `MinimumDiameterSpanningTreeResult(...)` | Result of a minimum-diameter spanning tree query. | Space: ``O(n)`` |
| `minimum_diameter_spanning_tree` | function | `minimum_diameter_spanning_tree(graph: Graph) -> MinimumDiameterSpanningTreeResult` | Find a spanning tree with minimum possible diameter. | Time: Dominated by all-pairs Dijkstra: typically ``O(n m log n + n^3)`` |

### `toptree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `TopTree` | class | `TopTree(values: Sequence[ValueT], point_identity: PointT, add_vertex: Callable[[PointT, ValueT]…` | Maintain tree DP on a forest under links, cuts, and point updates. | Space: O(n), assuming O(1)-size payloads and aggregates. Rake slots are reused and never grow with the number of queries. |
| `StaticTopTree` | class | `StaticTopTree(tree: Tree, values: Sequence[ValueT], point_identity: PointT, add_vertex: Callabl…` | Maintain tree DP under vertex updates on a fixed rooted tree. | Space: O(n), assuming O(1)-size values and aggregates. |
| `StaticTopTreeWithEdges` | class | `StaticTopTreeWithEdges(tree: Tree, vertex_values: Sequence[VertexValueT], edge_values: Sequence…` | Manage fixed-root tree DP with separate vertex and edge payloads. | Space: O(n), assuming O(1)-size payloads and aggregates. |
| `TopTreeWithEdges` | class | `TopTreeWithEdges(vertex_values: Sequence[VertexValueT], edges: Sequence[tuple[int, int]], edge_…` | Manage dynamic tree DP with separate vertex and edge payloads. | Space: O(n + m), for n original vertices and m edge slots, with O(1) payloads. |

### `tree.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `TreeDiameterResult` | class | `TreeDiameterResult(...)` | Result of one tree-diameter query. | Space: ``O(n)`` |
| `tree_diameter` | function | `tree_diameter(tree: Tree) -> TreeDiameterResult` | Compute the diameter of a tree with non-negative edge weights. | Time: ``O(n)`` |
| `tree_distance_frequency_table` | function | `tree_distance_frequency_table(tree: Tree) -> list[int]` | Count unordered vertex pairs by unweighted tree distance. | Time: ``O(n log^2 n)``, dominated by centroid-decomposition convolutions. |
| `TreeHashContext` | class | `TreeHashContext()` | Collision-free canonical IDs for rooted and unrooted unlabeled trees. | Space: O(k), where ``k`` is the number of distinct canonical forms interned in this context. |
| `BinaryTreeInfo` | class | `BinaryTreeInfo(...)` | Metadata for a binary tree represented by child arrays. | Space: O(n) |
| `BinaryTreeTraversal` | class | `BinaryTreeTraversal(...)` | Traversal orders of a binary tree. | Space: O(n) |
| `binary_tree_info` | function | `binary_tree_info(left: Sequence[int], right: Sequence[int]) -> BinaryTreeInfo` | Compute metadata for a binary tree represented by child arrays. | Time: O(n) |
| `binary_tree_traversals` | function | `binary_tree_traversals(left: Sequence[int], right: Sequence[int], root: int \| None = None) -> B…` | Return preorder, inorder, and postorder traversals of a binary tree. | Time: O(n) |
| `reconstruct_postorder_from_preorder_inorder` | function | `reconstruct_postorder_from_preorder_inorder(preorder: Sequence[T], inorder: Sequence[T]) -> lis…` | Reconstruct postorder traversal from preorder and inorder traversals. | Time: O(n) |

### `treedecomp.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `HeavyLightDecomposition` | class | `HeavyLightDecomposition(tree: Tree)` | Heavy-light decomposition of a built rooted tree. | Space: ``O(n)`` |
| `CentroidDecomposition` | class | `CentroidDecomposition(tree: Tree)` | Centroid decomposition of a static tree. | Space: ``O(n)`` |
| `SparseTableLCA` | class | `SparseTableLCA(tree: Tree)` | Lowest common ancestor by Euler tour and sparse table. | Space: ``O(n log n)`` |
| `LinearTimeLCA` | class | `LinearTimeLCA(tree: Tree)` | Lowest common ancestor by ``±1`` RMQ in linear preprocessing time. | Space: ``O(n)`` |

### `treedp.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `rerooting_dp` | function | `rerooting_dp(tree: Tree, ie: ValueT, merge: Callable[[ValueT, ValueT], ValueT], put_edge: Calla…` | Compute all-roots DP values with the rerooting technique. | Time: ``O(n)``, assuming each callback runs in ``O(1)`` |
| `FixedRootTreeDP` | class | `FixedRootTreeDP(tree: Tree, vertex_values: Sequence[VertexValueT], edge_values: Sequence[EdgeVa…` | Maintain a DP under vertex and edge updates on a fixed rooted tree. | Space: ``O(n)`` |

### `treequery.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `DSUOnTree` | class | `DSUOnTree(tree: Tree)` | Reusable executor for subtree queries on a rooted tree. | Space: ``O(n)`` |
| `VirtualTreeResult` | class | `VirtualTreeResult(...)` | Result of one virtual-tree construction. | Space: ``O(n + k)``, where ``n`` counts original vertices and ``k`` counts virtual nodes. ``virtual_id`` always has length ``n``. |
| `VirtualTreeBuilder` | class | `VirtualTreeBuilder(tree: Tree)` | Build virtual trees from repeated subset queries on one rooted tree. | Space: ``O(n)`` n is the number of vertices in the original tree. |
| `TreePathQuery` | class | `TreePathQuery(tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], e:…` | Support path and subtree folds on a static rooted tree. | Space: ``O(n)`` |
| `RangeContourSum` | class | `RangeContourSum(tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], i…` | Point-add, range-contour aggregation on a tree. | Space: ``O(n log n)`` |
| `RangeContourAdd` | class | `RangeContourAdd(tree: Tree, values: Sequence[ValueT], op: Callable[[ValueT, ValueT], ValueT], i…` | Range-contour add and point get on a tree. | Space: ``O(n log n)`` |

### `walk.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `DepthFirstSearchResult` | class | `DepthFirstSearchResult(...)` | Discovery and finish metadata of a depth-first search forest. | Space: O(n) |
| `depth_first_search` | function | `depth_first_search(graph: Graph, starts: Sequence[Node] \| None = None) -> DepthFirstSearchResult` | Run DFS and return discovery and finish times. | Time: O(n + m) |
| `CycleDetectionResult` | class | `CycleDetectionResult(...)` | Result of cycle detection. | Space: ``O(k)``, where ``k`` is the reported cycle length. |
| `cycle_detection` | function | `cycle_detection(graph: Graph) -> CycleDetectionResult` | Detect one cycle in a graph. | Time: ``O(n + m)`` |
| `EulerianTrailResult` | class | `EulerianTrailResult(...)` | Result of an Eulerian trail query. | Space: ``O(n + m)`` for the reported trail. |
| `eulerian_trail` | function | `eulerian_trail(graph: Graph) -> EulerianTrailResult` | Find one Eulerian trail using Hierholzer's algorithm. | Time: ``O(n + m)`` |
| `k_shortest_walk` | function | `k_shortest_walk(graph: Graph, source: Node, target: Node, k: int) -> list[Weight]` | Return the first ``k`` shortest walk lengths from ``source`` to ``target``. | Time: ``O((n + m) log n + k log k)`` |
