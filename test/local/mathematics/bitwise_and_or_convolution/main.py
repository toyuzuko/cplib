from cplib.mathematics.subset import BitwiseAndConvolution, BitwiseOrConvolution


def solve(inp: str) -> str:
    lines = inp.splitlines()
    if not lines:
        return ''
    n = int(lines[0])
    a = list(map(int, lines[1].split()))
    b = list(map(int, lines[2].split()))
    and_conv = BitwiseAndConvolution.convolution(n, a, b)
    or_conv = BitwiseOrConvolution.convolution(n, a, b)
    return ' '.join(map(str, and_conv)) + '\n' + ' '.join(map(str, or_conv)) + '\n'


if __name__ == '__main__':
    import sys

    sys.stdout.write(solve(sys.stdin.read()))
