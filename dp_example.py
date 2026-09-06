"""Simple dynamic programming example: Fibonacci with memoization.

Referenced from SCRUM-1 (seif hassan task).
"""


def fibonacci(n: int, memo: dict[int, int] | None = None) -> int:
    """Return the nth Fibonacci number using top-down DP (memoization)."""
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n not in memo:
        memo[n] = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
    return memo[n]


if __name__ == "__main__":
    n = 10
    print(f"Fibonacci({n}) = {fibonacci(n)}")