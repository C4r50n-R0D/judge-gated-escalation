"""Judge calibration, ensembles and calibration metrics (KICKOFF2 T21). Standard library only.

  brier(ps, ys), ece(ps, ys, bins=10)          calibration metrics
  fit_platt(ps, ys) -> (a, b)                   p' = sigmoid(a * logit(p) + b), fitted by Newton's method
  fit_isotonic(ps, ys) -> [(x, y), ...]         pool-adjacent-violators; apply with step interpolation
  fit_logreg(X, ys, l2) -> weights              logistic regression for stacking (intercept first)

Every fit is made on CALIBRATION rows only (tools/derived_judges.py enforces it) and then applied unchanged to
other rows. None of this feeds the confirmatory analysis: derived judges are exploratory (PREREG v2 section 11).
"""
import math

EPS = 1e-6


def clip(p): return min(1 - EPS, max(EPS, p))
def logit(p): p = clip(p); return math.log(p / (1 - p))
def sigmoid(z): return 1 / (1 + math.exp(-z)) if z > -700 else 0.0


def brier(ps, ys): return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps) if ps else None


def ece(ps, ys, bins=10):
    """Expected calibration error with equal-width bins: sum over bins of (bin share) x |mean p - accuracy|."""
    if not ps: return None
    tot = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, p in enumerate(ps) if (lo <= p < hi) or (b == bins - 1 and p == 1.0)]
        if idx: tot += len(idx) / len(ps) * abs(sum(ps[i] for i in idx) / len(idx) - sum(ys[i] for i in idx) / len(idx))
    return tot


def fit_logreg(X, ys, l2=1e-3, iters=50):
    """Newton-Raphson logistic regression with a small L2 penalty (not on the intercept). X rows without intercept."""
    n, d = len(X), (len(X[0]) if X else 0) + 1
    w = [0.0] * d
    Z = [[1.0] + list(x) for x in X]
    for _ in range(iters):
        g = [0.0] * d; H = [[0.0] * d for _ in range(d)]
        for z, y in zip(Z, ys):
            p = sigmoid(sum(wi * zi for wi, zi in zip(w, z))); r = p * (1 - p)
            for i in range(d):
                g[i] += (p - y) * z[i]
                for j in range(d): H[i][j] += r * z[i] * z[j]
        for i in range(1, d): g[i] += l2 * w[i]; H[i][i] += l2
        for i in range(d): H[i][i] += 1e-9
        step = solve(H, g)
        w = [wi - si for wi, si in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8: break
    return w


def solve(A, b):
    """Gaussian elimination with partial pivoting (small systems only)."""
    n = len(b); M = [row[:] + [bb] for row, bb in zip(A, b)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-15: continue
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-15 else 0.0 for i in range(n)]


def predict_logreg(w, x): return sigmoid(w[0] + sum(wi * xi for wi, xi in zip(w[1:], x)))


def fit_platt(ps, ys):
    w = fit_logreg([[logit(p)] for p in ps], ys, l2=0.0)
    return w[1], w[0]


def apply_platt(ab, p): return sigmoid(ab[0] * logit(p) + ab[1])


def fit_isotonic(ps, ys):
    """Pool-adjacent-violators on (p, y) sorted by p. Returns knots [(p_max_of_block, fitted_value), ...]."""
    pts = sorted(zip(ps, ys))
    blocks = []   # [sum_y, count, max_p]
    for p, y in pts:
        blocks.append([float(y), 1, p])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s, c, m = blocks.pop(); blocks[-1][0] += s; blocks[-1][1] += c; blocks[-1][2] = m
    return [(m, s / c) for s, c, m in blocks]


def apply_isotonic(knots, p):
    for m, v in knots:
        if p <= m: return v
    return knots[-1][1] if knots else p
