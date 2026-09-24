# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/8/ITP2/1/ITP2_1_C

from cplib.datastructure.linkedlist import DoublyLinkedList
from cplib.tools.fastio import FastIO


Q = FastIO.read_int()
L = DoublyLinkedList[int]()
cursor = 0

for _ in range(Q):
    com = FastIO.read_int()
    if com == 0:
        cursor = L.insert_before(cursor, FastIO.read_int())
    elif com == 1:
        d = FastIO.read_int()
        if d > 0:
            for _ in range(d):
                cursor = L.next_node(cursor)
        else:
            for _ in range(-d):
                cursor = L.prev_node(cursor)
    else:
        _, cursor = L.erase(cursor)

for x in L.to_list():
    FastIO.writeln(f'{x}')
