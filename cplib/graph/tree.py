"""Static tree algorithms: diameter, distance distribution, isomorphism, and binary-tree traversal."""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from cplib.graph.base import Node, Weight
from cplib.graph.core import Tree
from cplib.graph.treedecomp import CentroidDecomposition
from cplib.mathematics.convolution import ConvolutionLargeIntegers
from cplib.tools.type import T

__all__ = ['TreeDiameterResult', 'tree_diameter', 'tree_distance_frequency_table', 'TreeHashContext', 'BinaryTreeInfo', 'BinaryTreeTraversal', 'binary_tree_info', 'binary_tree_traversals', 'reconstruct_postorder_from_preorder_inorder']


class TreeDiameterResult(NamedTuple):
    """
    Result of one tree-diameter query.

    Attributes:
        start: One endpoint of the diameter.
        end: The other endpoint of the diameter.
        distance: Total weighted distance on the diameter.
        path: Vertices on one diameter path from ``start`` to ``end``.

    The path includes both endpoints.
    Either endpoint may be chosen when multiple diameters exist.
    The distance uses the same weight type as the input tree.

    Space Complexity:
        - ``O(n)``
    """

    start: Node
    end: Node
    distance: Weight
    path: list[Node]


def _tree_farthest(tree: Tree, start: int) -> tuple[int, list[int], list[int]]:
    parent = [-1] * tree.n
    dist = [0] * tree.n
    stack = [start]
    parent[start] = start
    visited = 0
    while stack:
        vertex = stack.pop()
        visited += 1
        for to, edge_id in tree.tree[vertex]:
            next_vertex = int(to)
            if parent[vertex] == next_vertex:
                continue
            if parent[next_vertex] != -1:
                continue
            parent[next_vertex] = vertex
            dist[next_vertex] = dist[vertex] + int(tree.wt[edge_id])
            stack.append(next_vertex)
    if visited != tree.n:
        raise ValueError('tree must be connected')
    farthest = start
    for vertex in range(tree.n):
        if dist[vertex] > dist[farthest]:
            farthest = vertex
    parent[start] = -1
    return farthest, parent, dist


def tree_diameter(tree: Tree) -> TreeDiameterResult:
    """
    Compute the diameter of a tree with non-negative edge weights.

    Args:
        tree: Tree with non-negative edge weights whose diameter is requested.

    Returns:
        TreeDiameterResult: Endpoints, weighted distance, and one diameter path.

    Raises:
        ValueError: If the input is empty, disconnected, not a tree, or has a negative edge.

    Time Complexity:
        - ``O(n)``

    Space Complexity:
        - ``O(n)``
    """
    if tree.n == 0:
        raise ValueError('tree must contain at least one vertex')
    if tree.m != tree.n - 1:
        raise ValueError('tree must contain exactly n - 1 edges')
    if any(weight < 0 for weight in tree.wt):
        raise ValueError('tree diameter requires non-negative edge weights')
    if tree.n == 1:
        return TreeDiameterResult(start=Node(0), end=Node(0), distance=Weight(0), path=[Node(0)])
    start, _, _ = _tree_farthest(tree, 0)
    end, parent, dist = _tree_farthest(tree, start)
    path_ints: list[int] = []
    vertex = end
    while vertex != -1:
        path_ints.append(vertex)
        if vertex == start:
            break
        vertex = parent[vertex]
    path_ints.reverse()
    return TreeDiameterResult(
        start=Node(start),
        end=Node(end),
        distance=Weight(dist[end]),
        path=[Node(vertex) for vertex in path_ints],
    )


def tree_distance_frequency_table(tree: Tree) -> list[int]:
    """
    Count unordered vertex pairs by unweighted tree distance.

    Args:
        tree: Unweighted tree.

    Returns:
        ``ans`` where ``ans[d]`` is the number of unordered pairs ``(u, v)``
        such that ``u < v`` and the number of edges on the path from ``u`` to
        ``v`` is ``d``. ``ans[0]`` is always ``0``.

    Raises:
        ValueError: If the input is empty, disconnected, or does not have
            ``n - 1`` edges.

    Time Complexity:
        ``O(n log^2 n)``, dominated by centroid-decomposition convolutions.

    Space Complexity:
        ``O(n log n)`` for the centroid decomposition and transform buffers.
    """
    n = tree.n
    if n == 0:
        raise ValueError('tree must contain at least one vertex')
    if tree.m != n - 1:
        raise ValueError('tree must contain exactly n - 1 edges')
    seen = [False] * n
    seen[0] = True
    stack = [0]
    visited = 0
    while stack:
        vertex = stack.pop()
        visited += 1
        for to, _ in tree.tree[vertex]:
            next_vertex = int(to)
            if seen[next_vertex]:
                continue
            seen[next_vertex] = True
            stack.append(next_vertex)
    if visited != n:
        raise ValueError('tree must be connected')

    ordered = [0] * n

    def add_depth_pairs(counts: list[int], sign: int) -> None:
        conv = ConvolutionLargeIntegers.convolution(counts, counts)
        limit = min(n, len(conv))
        for dist in range(1, limit):
            ordered[dist] += sign * conv[dist]

    def process_centroid(cd: CentroidDecomposition, centroid: Node) -> None:
        counts: list[int] = []
        for vertex in cd.dfs_order:
            depth = cd.dep[vertex]
            while len(counts) <= depth:
                counts.append(0)
            counts[depth] += 1
        add_depth_pairs(counts, 1)

    def process_child(cd: CentroidDecomposition, centroid: Node, root: Node, start_idx: int, end_idx: int) -> None:
        counts: list[int] = []
        for idx in range(start_idx, end_idx):
            depth = cd.dep[cd.dfs_order[idx]]
            while len(counts) <= depth:
                counts.append(0)
            counts[depth] += 1
        add_depth_pairs(counts, -1)

    CentroidDecomposition.build_with_callbacks(tree, process_centroid, process_child)

    for dist in range(1, n):
        ordered[dist] //= 2
    return ordered


class TreeHashContext:
    """
    Collision-free canonical IDs for rooted and unrooted unlabeled trees.

    IDs are consistent across every tree processed by the same context. This
    makes the context suitable for comparing subtrees inside one tree and for
    comparing multiple independent ``Tree`` instances.

    Space Complexity:
        O(k), where ``k`` is the number of distinct canonical forms interned in
        this context.
    """

    def __init__(self) -> None:
        """
        Initialize an empty canonical-form context.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self._rooted_ids: dict[tuple[int, ...], int] = {}
        self._unrooted_vertex_ids: dict[int, int] = {}
        self._unrooted_edge_ids: dict[tuple[int, int], int] = {}

    def _rooted_id(self, child_ids: list[int]) -> int:
        child_ids.sort()
        key = tuple(child_ids)
        value = self._rooted_ids.get(key)
        if value is None:
            value = len(self._rooted_ids)
            self._rooted_ids[key] = value
        return value

    def _unrooted_vertex_id(self, rooted_id: int) -> int:
        value = self._unrooted_vertex_ids.get(rooted_id)
        if value is None:
            value = len(self._unrooted_vertex_ids) + len(self._unrooted_edge_ids)
            self._unrooted_vertex_ids[rooted_id] = value
        return value

    def _unrooted_edge_id(self, id1: int, id2: int) -> int:
        if id1 > id2:
            id1, id2 = id2, id1
        key = (id1, id2)
        value = self._unrooted_edge_ids.get(key)
        if value is None:
            value = len(self._unrooted_vertex_ids) + len(self._unrooted_edge_ids)
            self._unrooted_edge_ids[key] = value
        return value

    @staticmethod
    def _validate_tree(tree: Tree) -> None:
        if tree.n == 0:
            raise ValueError('tree must contain at least one vertex')
        if tree.m != tree.n - 1:
            raise ValueError('tree must contain exactly n - 1 edges')

    @staticmethod
    def _root_order(tree: Tree, root: int, blocked: int = -1) -> tuple[list[int], list[int]]:
        parent = [-2] * tree.n
        parent[root] = blocked
        order = [root]
        stack = [root]
        while stack:
            vertex = stack.pop()
            for to, _ in tree.tree[vertex]:
                nxt = int(to)
                if nxt == parent[vertex] or nxt == blocked:
                    continue
                if parent[nxt] != -2:
                    continue
                parent[nxt] = vertex
                order.append(nxt)
                stack.append(nxt)
        return order, parent

    def rooted_subtree_ids(self, tree: Tree, root: Node = Node(0)) -> list[int]:
        """
        Return canonical IDs of all rooted subtrees.

        The tree is rooted at ``root``. For vertices ``u`` and ``v``, returned
        IDs are equal if and only if the rooted subtrees of ``u`` and ``v`` are
        isomorphic.

        Args:
            tree: Unlabeled tree.
            root: Root vertex.

        Returns:
            Canonical rooted-subtree ID for each vertex.

        Raises:
            ValueError: If ``tree`` is empty or does not have ``n - 1`` edges.
            IndexError: If ``root`` is outside ``[0, n)``.
            ValueError: If ``tree`` is disconnected.

        Time Complexity:
            O(n log n), dominated by sorting child IDs at each vertex.

        Space Complexity:
            O(n)
        """
        self._validate_tree(tree)
        r = int(root)
        if not 0 <= r < tree.n:
            raise IndexError('root must be within [0, n)')
        order, parent = self._root_order(tree, r)
        if len(order) != tree.n:
            raise ValueError('tree must be connected')
        ids = [-1] * tree.n
        for vertex in reversed(order):
            child_ids = [ids[int(to)] for to, _ in tree.tree[vertex] if parent[int(to)] == vertex]
            ids[vertex] = self._rooted_id(child_ids)
        return ids

    def rooted_tree_id(self, tree: Tree, root: Node = Node(0)) -> int:
        """
        Return the canonical ID of a rooted tree.

        Args:
            tree: Unlabeled tree.
            root: Root vertex.

        Returns:
            Canonical rooted-tree ID.

        Time Complexity:
            O(n log n)

        Space Complexity:
            O(n)
        """
        return self.rooted_subtree_ids(tree, root)[int(root)]

    def _rooted_component_id(self, tree: Tree, root: int, blocked: int) -> int:
        order, parent = self._root_order(tree, root, blocked)
        ids = [-1] * tree.n
        for vertex in reversed(order):
            child_ids = [ids[int(to)] for to, _ in tree.tree[vertex] if parent[int(to)] == vertex]
            ids[vertex] = self._rooted_id(child_ids)
        return ids[root]

    def _centers(self, tree: Tree) -> tuple[int, ...]:
        degree = [len(tree.tree[v]) for v in range(tree.n)]
        leaves = [v for v in range(tree.n) if degree[v] <= 1]
        remaining = tree.n
        while remaining > 2:
            remaining -= len(leaves)
            next_leaves: list[int] = []
            for leaf in leaves:
                for to, _ in tree.tree[leaf]:
                    nxt = int(to)
                    degree[nxt] -= 1
                    if degree[nxt] == 1:
                        next_leaves.append(nxt)
            leaves = next_leaves
        return tuple(sorted(leaves))

    def unrooted_tree_id(self, tree: Tree) -> int:
        """
        Return the canonical ID of an unrooted tree.

        IDs returned by this method are separate from rooted-tree IDs. Two
        unrooted trees have equal IDs if and only if they are isomorphic.

        Args:
            tree: Unlabeled tree.

        Returns:
            Canonical unrooted-tree ID.

        Raises:
            ValueError: If ``tree`` is empty, disconnected, or not a tree.

        Time Complexity:
            O(n log n)

        Space Complexity:
            O(n)
        """
        self._validate_tree(tree)
        order, _ = self._root_order(tree, 0)
        if len(order) != tree.n:
            raise ValueError('tree must be connected')
        if tree.n == 1:
            return self._unrooted_vertex_id(self._rooted_id([]))
        centers = self._centers(tree)
        if len(centers) == 1:
            rooted_id = self.rooted_tree_id(tree, Node(centers[0]))
            return self._unrooted_vertex_id(rooted_id)
        c1, c2 = centers
        id1 = self._rooted_component_id(tree, c1, c2)
        id2 = self._rooted_component_id(tree, c2, c1)
        return self._unrooted_edge_id(id1, id2)

    def are_rooted_isomorphic(self, tree1: Tree, root1: Node, tree2: Tree, root2: Node) -> bool:
        """
        Return whether two rooted trees are isomorphic.

        Args:
            tree1: First tree.
            root1: Root of the first tree.
            tree2: Second tree.
            root2: Root of the second tree.

        Returns:
            True if the rooted trees are isomorphic.

        Time Complexity:
            O((n + m) log(n + m))

        Space Complexity:
            O(n + m)
        """
        if tree1.n != tree2.n:
            return False
        return self.rooted_tree_id(tree1, root1) == self.rooted_tree_id(tree2, root2)

    def are_unrooted_isomorphic(self, tree1: Tree, tree2: Tree) -> bool:
        """
        Return whether two unrooted trees are isomorphic.

        Args:
            tree1: First tree.
            tree2: Second tree.

        Returns:
            True if the unrooted trees are isomorphic.

        Time Complexity:
            O((n + m) log(n + m))

        Space Complexity:
            O(n + m)
        """
        if tree1.n != tree2.n:
            return False
        return self.unrooted_tree_id(tree1) == self.unrooted_tree_id(tree2)


class BinaryTreeInfo(NamedTuple):
    """
    Metadata for a binary tree represented by child arrays.

    Attributes:
        root: Root vertex, or ``-1`` if the tree is empty.
        parent: Parent of each vertex, or ``-1`` for the root.
        sibling: Sibling of each vertex, or ``-1`` if absent.
        degree: Number of children of each vertex.
        depth: Depth of each vertex from the root.
        height: Height of each vertex.

    Space Complexity:
        O(n)
    """

    root: int
    parent: list[int]
    sibling: list[int]
    degree: list[int]
    depth: list[int]
    height: list[int]


class BinaryTreeTraversal(NamedTuple):
    """
    Traversal orders of a binary tree.

    Attributes:
        preorder: Root-left-right order.
        inorder: Left-root-right order.
        postorder: Left-right-root order.

    Space Complexity:
        O(n)
    """

    preorder: list[int]
    inorder: list[int]
    postorder: list[int]


def binary_tree_info(left: Sequence[int], right: Sequence[int]) -> BinaryTreeInfo:
    """
    Compute metadata for a binary tree represented by child arrays.

    Args:
        left: ``left[v]`` is the left child of ``v``, or ``-1``.
        right: ``right[v]`` is the right child of ``v``, or ``-1``.

    Returns:
        BinaryTreeInfo containing root, parent, sibling, degree, depth, and height arrays.

    Raises:
        ValueError: If ``left`` and ``right`` have different lengths.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    n = len(left)
    if len(right) != n:
        raise ValueError('left and right must have the same length')
    parent = [-1] * n
    sibling = [-1] * n
    degree = [0] * n

    for v in range(n):
        l = left[v]
        r = right[v]
        if l != -1:
            parent[l] = v
            degree[v] += 1
        if r != -1:
            parent[r] = v
            degree[v] += 1
        if l != -1 and r != -1:
            sibling[l] = r
            sibling[r] = l

    root = -1
    for v in range(n):
        if parent[v] == -1:
            root = v
            break

    depth = [-1] * n
    height = [0] * n
    if root != -1:
        depth[root] = 0
        stack = [root]
        order: list[int] = []
        while stack:
            v = stack.pop()
            order.append(v)
            r = right[v]
            l = left[v]
            if r != -1:
                depth[r] = depth[v] + 1
                stack.append(r)
            if l != -1:
                depth[l] = depth[v] + 1
                stack.append(l)
        for v in reversed(order):
            h = 0
            if left[v] != -1:
                h = max(h, height[left[v]] + 1)
            if right[v] != -1:
                h = max(h, height[right[v]] + 1)
            height[v] = h

    return BinaryTreeInfo(root, parent, sibling, degree, depth, height)


def binary_tree_traversals(left: Sequence[int], right: Sequence[int], root: int | None = None) -> BinaryTreeTraversal:
    """
    Return preorder, inorder, and postorder traversals of a binary tree.

    Args:
        left: ``left[v]`` is the left child of ``v``, or ``-1``.
        right: ``right[v]`` is the right child of ``v``, or ``-1``.
        root: Root vertex. If omitted, it is inferred from the parent relation.

    Returns:
        BinaryTreeTraversal containing the three traversal orders.

    Raises:
        ValueError: If ``left`` and ``right`` have different lengths.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    n = len(left)
    if len(right) != n:
        raise ValueError('left and right must have the same length')
    if root is None:
        root = binary_tree_info(left, right).root
    if root == -1:
        return BinaryTreeTraversal([], [], [])

    preorder: list[int] = []
    stack = [root]
    while stack:
        v = stack.pop()
        preorder.append(v)
        if right[v] != -1:
            stack.append(right[v])
        if left[v] != -1:
            stack.append(left[v])

    inorder: list[int] = []
    stack: list[int] = []
    v = root
    while v != -1 or stack:
        while v != -1:
            stack.append(v)
            v = left[v]
        v = stack.pop()
        inorder.append(v)
        v = right[v]

    postorder: list[int] = []
    stack2: list[tuple[int, bool]] = [(root, False)]
    while stack2:
        v, visited = stack2.pop()
        if visited:
            postorder.append(v)
            continue
        stack2.append((v, True))
        if right[v] != -1:
            stack2.append((right[v], False))
        if left[v] != -1:
            stack2.append((left[v], False))

    return BinaryTreeTraversal(preorder, inorder, postorder)


def reconstruct_postorder_from_preorder_inorder(preorder: Sequence[T], inorder: Sequence[T]) -> list[T]:
    """
    Reconstruct postorder traversal from preorder and inorder traversals.

    The input tree must have distinct vertex labels.

    Args:
        preorder: Root-left-right traversal.
        inorder: Left-root-right traversal.

    Returns:
        Left-right-root traversal.

    Raises:
        ValueError: If the traversal lengths differ or are inconsistent.

    Time Complexity:
        O(n)

    Space Complexity:
        O(n)
    """
    n = len(preorder)
    if len(inorder) != n:
        raise ValueError('preorder and inorder must have the same length')
    pos = {value: i for i, value in enumerate(inorder)}
    if len(pos) != n:
        raise ValueError('labels must be distinct')

    postorder: list[T] = []
    stack: list[tuple[int, int, int, int, int]] = [(0, n, 0, n, 0)]
    while stack:
        pre_l, pre_r, in_l, in_r, state = stack.pop()
        if pre_l == pre_r:
            continue
        root = preorder[pre_l]
        if state:
            postorder.append(root)
            continue
        if root not in pos:
            raise ValueError('traversals are inconsistent')
        in_root = pos[root]
        if not (in_l <= in_root < in_r):
            raise ValueError('traversals are inconsistent')
        left_size = in_root - in_l
        if pre_l + 1 + left_size > pre_r:
            raise ValueError('traversals are inconsistent')
        stack.append((pre_l, pre_r, in_l, in_r, 1))
        stack.append((pre_l + 1 + left_size, pre_r, in_root + 1, in_r, 0))
        stack.append((pre_l + 1, pre_l + 1 + left_size, in_l, in_root, 0))
    return postorder
