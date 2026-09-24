# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/lesson/1/ALDS1/9/ALDS1_9_C

from cplib.datastructure.queue import PriorityQueue
from cplib.tools.fastio import FastIO


heap = PriorityQueue[int](ascending=False)

while True:
    command = FastIO.read()
    if command == 'insert':
        heap.push(FastIO.read_int())
    elif command == 'extract':
        FastIO.writeln(f'{heap.pop()}')
    else:
        break
