# verification-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/problems/2439

# AOJ 2439 Hakone
# 箱根駅伝DP

MOD = 1000000007

N = int(input())
C = [input() for _ in range(N)] # 'U' or 'D' or '-'

'''
dp[i][j]: 現在の通過順にi番目までの順位変動をみたときに、保留している数がj個であるときの、ありえた前の中継所の通過順の数
'''

dp = [[0 for _ in range(N + 1)] for _ in range(N + 1)]
dp[0][0] = 1

for i in range(N):
    for j in range(N):
        if C[i] == 'U': # 現在i位の走者を保留する
            # 前回i位の走者を、保留していた現在の走者とマッチさせる
            if j > 0:
                dp[i + 1][j] += dp[i][j] * j
                dp[i + 1][j] %= MOD
            # 前回i位の走者を、保留する
            if j + 1 <= N:
                dp[i + 1][j + 1] += dp[i][j]
                dp[i + 1][j + 1] %= MOD
        elif C[i] == 'D': # 現在i位の走者を、保留していた前回の走者とマッチさせる
            # 前回i位の走者を、保留していた現在の走者とマッチさせる
            if j > 0:
                dp[i + 1][j - 1] += dp[i][j] * j * j
                dp[i + 1][j - 1] %= MOD
            # 前回i位の走者を、保留する
            if j > 0:
                dp[i + 1][j] += dp[i][j] * j
                dp[i + 1][j] %= MOD
        else: # 現在i位の走者と、前回i位の走者をマッチさせる
            dp[i + 1][j] += dp[i][j]
            dp[i + 1][j] %= MOD

print(dp[N][0])
