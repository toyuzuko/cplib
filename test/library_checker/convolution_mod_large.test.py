# verification-helper: PROBLEM https://judge.yosupo.jp/problem/convolution_mod_large

from cplib.mathematics.convolution import ConvolutionMod


MOD = 998244353
LIM = 1 << 23 # 998244353 = 2^23

def convolution_large(A: list[int], B: list[int]) -> list[int]:
    N, M = len(A), len(B)
    block_size = (LIM + 1) // 2
    res = [0] * (N + M - 1)
    for i in range((N + block_size - 1) // block_size):
        al = i * block_size
        ar = min(al + block_size, N)
        for j in range((M + block_size - 1) // block_size):
            bl = j * block_size
            br = min(bl + block_size, M)
            part = ConvolutionMod.convolution(A[al:ar], B[bl:br])
            base = al + bl
            for k, v in enumerate(part):
                res[base + k] = (res[base + k] + v) % MOD
    return res

N, M = map(int, input().split())
A = list(map(int, input().split()))
B = list(map(int, input().split()))

conv = convolution_large(A, B)

print(*conv)