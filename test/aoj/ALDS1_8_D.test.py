# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/8/ALDS1_8_D

from collections.abc import Iterator

from cplib.tools.fastio import FastIO


class ExplicitTreap:
    __slots__ = ['root', 'key', 'priority', 'left', 'right']

    def __init__(self) -> None:
        self.root = 0
        self.key = [-1]
        self.priority = [-1]
        self.left = [0]
        self.right = [0]

    def _new_node(self, key: int, priority: int) -> int:
        node = len(self.key)
        self.key.append(key)
        self.priority.append(priority)
        self.left.append(0)
        self.right.append(0)
        return node

    def _rotate_right(self, node: int) -> int:
        new_root = self.left[node]
        self.left[node] = self.right[new_root]
        self.right[new_root] = node
        return new_root

    def _rotate_left(self, node: int) -> int:
        new_root = self.right[node]
        self.right[node] = self.left[new_root]
        self.left[new_root] = node
        return new_root

    def _set_child(self, parent: int, old_child: int, new_child: int) -> None:
        if parent == 0:
            self.root = new_child
        elif self.left[parent] == old_child:
            self.left[parent] = new_child
        else:
            self.right[parent] = new_child

    def insert(self, key: int, priority: int) -> None:
        if self.root == 0:
            self.root = self._new_node(key, priority)
            return

        path: list[int] = []
        node = self.root
        while node:
            path.append(node)
            if key == self.key[node]:
                return
            if key < self.key[node]:
                nxt = self.left[node]
                if nxt == 0:
                    child = self._new_node(key, priority)
                    self.left[node] = child
                    path.append(child)
                    break
                node = nxt
            else:
                nxt = self.right[node]
                if nxt == 0:
                    child = self._new_node(key, priority)
                    self.right[node] = child
                    path.append(child)
                    break
                node = nxt

        child = path[-1]
        while len(path) >= 2:
            parent = path[-2]
            if self.priority[parent] >= self.priority[child]:
                break
            grandparent = path[-3] if len(path) >= 3 else 0
            if self.left[parent] == child:
                new_subroot = self._rotate_right(parent)
            else:
                new_subroot = self._rotate_left(parent)
            self._set_child(grandparent, parent, new_subroot)
            path.pop(-2)

    def delete(self, key: int) -> None:
        parent = 0
        node = self.root
        while node:
            if key == self.key[node]:
                break
            parent = node
            node = self.left[node] if key < self.key[node] else self.right[node]
        if node == 0:
            return

        while self.left[node] or self.right[node]:
            if self.left[node] == 0:
                new_subroot = self._rotate_left(node)
            elif self.right[node] == 0:
                new_subroot = self._rotate_right(node)
            elif self.priority[self.left[node]] > self.priority[self.right[node]]:
                new_subroot = self._rotate_right(node)
            else:
                new_subroot = self._rotate_left(node)
            self._set_child(parent, node, new_subroot)
            parent = new_subroot

        self._set_child(parent, node, 0)

    def contains(self, key: int) -> bool:
        node = self.root
        while node:
            if key == self.key[node]:
                return True
            node = self.left[node] if key < self.key[node] else self.right[node]
        return False

    def inorder(self) -> Iterator[int]:
        stack: list[int] = []
        node = self.root
        while stack or node:
            while node:
                stack.append(node)
                node = self.left[node]
            node = stack.pop()
            yield self.key[node]
            node = self.right[node]

    def preorder(self) -> Iterator[int]:
        if self.root == 0:
            return
        stack = [self.root]
        while stack:
            node = stack.pop()
            yield self.key[node]
            right = self.right[node]
            left = self.left[node]
            if right:
                stack.append(right)
            if left:
                stack.append(left)


M = FastIO.read_int()
tree = ExplicitTreap()

for _ in range(M):
    command = FastIO.read()
    if command == 'insert':
        tree.insert(FastIO.read_int(), FastIO.read_int())
    elif command == 'find':
        FastIO.writeln('yes' if tree.contains(FastIO.read_int()) else 'no')
    elif command == 'delete':
        tree.delete(FastIO.read_int())
    else:
        FastIO.writeln(' ' + ' '.join(map(str, tree.inorder())))
        FastIO.writeln(' ' + ' '.join(map(str, tree.preorder())))
