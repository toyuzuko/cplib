# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/problems/2574

from cplib.algorithm.sat import ThreeSatSolver
from cplib.tools.fastio import FastIO

while True:
    M = FastIO.read_int()
    if M == 0: break

    board = [FastIO.read().rstrip() for _ in range(3)]

    solver = ThreeSatSolver(26)

    for i in range(M):
        c1 = 3 * i + 1
        c2 = 3 * i + 2
        for mask in range(8):
            lits: list[tuple[int, bool]] = []
            for row in range(3):
                ch = board[row][c2] if (mask & (1 << row)) else board[row][c1]
                var_idx = ord(ch.upper()) - ord('A')
                val = ch.islower()
                lits.append((var_idx, val))
            (v1, b1), (v2, b2), (v3, b3) = lits
            solver.add_clause(v1, b1, v2, b2, v3, b3)

    result = solver.solve()

    if not result:
        FastIO.writeln('-1')
    else:
        assert result.assignment is not None
        pushes = [chr(ord('A') + i) for i, val in enumerate(result.assignment) if val]
        if len(pushes) > 0:
            FastIO.writeln(f'{len(pushes)} {" ".join(pushes)}')
        else:
            FastIO.writeln('0')
