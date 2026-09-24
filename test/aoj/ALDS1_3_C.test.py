# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/3/ALDS1_3_C

from cplib.datastructure.linkedlist import DoublyLinkedList
from cplib.tools.fastio import FastIO


N = FastIO.read_int()
linked_list = DoublyLinkedList[int]()

for _ in range(N):
    command = FastIO.read()
    if command == 'insert':
        linked_list.insert_front(FastIO.read_int())
    elif command == 'delete':
        linked_list.discard_first(FastIO.read_int())
    elif command == 'deleteFirst':
        linked_list.pop_front()
    else:
        linked_list.pop_back()

FastIO.writeln(' '.join(map(str, linked_list.to_list())))
