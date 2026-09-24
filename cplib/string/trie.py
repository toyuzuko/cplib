#!/usr/bin/env python3

from array import array
from collections.abc import Iterator


class Trie:
    """
    Trie for lowercase ASCII strings.

    The structure stores explicit trie edges and node metadata useful for
    prefix queries and tree DP.
    All inserted/query strings must contain only lowercase ``'a'`` through
    ``'z'`` characters.

    Let ``L`` be the total length of inserted words, ``V`` the number of trie
    nodes, and ``A`` the alphabet size.

    Args:
        None.

    Space Complexity:
        ``O(V * A)``.
    """
    alphabet_size = 26
    alphabet_base = ord('a')

    def __init__(self) -> None:
        """Initialize an empty trie.

        Returns:
            None.

        Time Complexity:
            ``O(A)``.

        Space Complexity:
            ``O(A)``.
        """
        self.trie = [array('i', [-1]) * self.alphabet_size]
        self.parent = array('i', [-1])
        self.parent_char = array('i', [-1])
        self.terminal_count: list[int] = [0]
        self.subtree_count: list[int] = [0]

    def _char_id(self, char: int | str) -> int:
        if isinstance(char, int):
            return char - self.alphabet_base
        return ord(char) - self.alphabet_base

    def _char_from_id(self, char_id: int) -> str:
        return chr(char_id + self.alphabet_base)

    def __len__(self) -> int:
        """Return the number of trie nodes.

        Returns:
            Number of nodes.

        Time Complexity:
            ``O(1)``.
        """
        return len(self.trie)

    def new_node(self, parent: int, char_id: int) -> int:
        """Allocate a trie node with parent metadata.

        This low-level operation does not connect the parent's child edge or
        add word counts. Use insert for ordinary word insertion.

        Args:
            parent: Parent node index.
            char_id: Edge label from parent as an integer in ``[0, A)``.

        Returns:
            New node index.

        Raises:
            IndexError: If parent or char_id is outside its valid range.

        Time Complexity:
            ``O(A)``.
        """
        if not (0 <= parent < len(self.trie) and 0 <= char_id < self.alphabet_size):
            raise IndexError('parent or char_id is out of range')
        node = len(self.trie)
        self.trie.append(array('i', [-1]) * self.alphabet_size)
        self.parent.append(parent)
        self.parent_char.append(char_id)
        self.terminal_count.append(0)
        self.subtree_count.append(0)
        return node

    def insert(self, word: str, count: int = 1) -> int:
        """Insert a word into the trie.

        Args:
            word: Word to insert.
            count: Non-negative multiplicity to add. Zero creates the path
                without recording an occurrence.

        Returns:
            Terminal node for ``word``.

        Raises:
            ValueError: If count is negative or word is not lowercase ASCII.

        Time Complexity:
            ``O(len(word))``.
        """
        if count < 0:
            raise ValueError('count must be non-negative')
        wb = word.encode('ascii')
        if wb and not (wb.isalpha() and wb.islower()):
            raise ValueError('word must contain only lowercase ASCII letters')
        node = 0
        path = [0]
        for b in wb:
            c = self._char_id(b)
            nxt = self.trie[node][c]
            if nxt == -1:
                nxt = self.new_node(node, c)
                self.trie[node][c] = nxt
            node = nxt
            path.append(node)
        if count:
            self.terminal_count[node] += count
            for v in path:
                self.subtree_count[v] += count
        return node

    def node(self, word: str) -> int:
        """Return the node reached by a word or prefix.

        Args:
            word: String to follow from the root.

        Returns:
            Node index, or ``-1`` if the path does not exist.

        Raises:
            ValueError: If word is not lowercase ASCII.

        Time Complexity:
            ``O(len(word))``.
        """
        node = 0
        wb = word.encode('ascii')
        if wb and not (wb.isalpha() and wb.islower()):
            raise ValueError('word must contain only lowercase ASCII letters')
        for b in wb:
            node = self.trie[node][self._char_id(b)]
            if node == -1:
                return -1
        return node

    def count(self, word: str) -> int:
        """Return the multiplicity of a word.

        Args:
            word: Word to count.

        Returns:
            Number of inserted copies of ``word``.

        Time Complexity:
            ``O(len(word))``.
        """
        node = self.node(word)
        return 0 if node == -1 else self.terminal_count[node]

    def contains(self, word: str) -> bool:
        """Return whether a word was inserted.

        Args:
            word: Word to check.

        Returns:
            True if ``word`` has positive multiplicity.

        Time Complexity:
            ``O(len(word))``.
        """
        return self.count(word) > 0

    def starts_with(self, prefix: str) -> bool:
        """Return whether any inserted word has the given prefix.

        Args:
            prefix: Prefix to check.

        Returns:
            True if the prefix path exists and has a terminal descendant.

        Time Complexity:
            ``O(len(prefix))``.
        """
        node = self.node(prefix)
        return node != -1 and self.subtree_count[node] > 0

    def prefix_count(self, prefix: str) -> int:
        """Return the number of inserted words with the given prefix.

        Args:
            prefix: Prefix to count.

        Returns:
            Total multiplicity of words with ``prefix``.

        Time Complexity:
            ``O(len(prefix))``.
        """
        node = self.node(prefix)
        return 0 if node == -1 else self.subtree_count[node]

    def children(self, node: int) -> Iterator[tuple[int, int]]:
        """Iterate over children of a node.

        Args:
            node: Source node.

        Yields:
            Pairs ``(char_id, child_node)``.

        Raises:
            IndexError: If node is outside the allocated node range.

        Time Complexity:
            ``O(A)``.
        """
        if not 0 <= node < len(self.trie):
            raise IndexError('node index out of range')
        for char_id, child in enumerate(self.trie[node]):
            if child != -1:
                yield char_id, child

    def dfs_order(self) -> list[int]:
        """Return nodes in preorder DFS order.

        Returns:
            List of node indices.

        Time Complexity:
            ``O(V * A)``.

        Space Complexity:
            ``O(V)``.
        """
        order: list[int] = []
        stack = [0]
        while stack:
            node = stack.pop()
            order.append(node)
            for _, child in reversed(list(self.children(node))):
                stack.append(child)
        return order

    def postorder(self) -> list[int]:
        """Return nodes in postorder.

        Returns:
            List of node indices with children before their parents.

        Time Complexity:
            ``O(V * A)``.

        Space Complexity:
            ``O(V)``.
        """
        return self.dfs_order()[::-1]

    def restore(self, node: int) -> str:
        """Restore the string represented by a node.

        Args:
            node: Trie node index.

        Returns:
            String on the path from the root to ``node``.

        Raises:
            IndexError: If node is outside the allocated node range.

        Time Complexity:
            ``O(depth(node))``.
        """
        if not 0 <= node < len(self.trie):
            raise IndexError('node index out of range')
        chars: list[str] = []
        while node:
            chars.append(self._char_from_id(self.parent_char[node]))
            node = self.parent[node]
        return ''.join(chars[::-1])
