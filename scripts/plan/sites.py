# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
import numpy as np, itertools
R = 3389.5  # km, Mars mean radius
PAST = [  # name, country, year, site, lat, lon(E), status
 ("Mars 3", "USSR", 1971, "Terra Sirenum", -45.0, 202.0, "partial"),
 ("Viking 1", "USA", 1976, "Chryse Planitia", 22.27, 312.05, "ended"),
 ("Viking 2", "USA", 1976, "Utopia Planitia", 47.64, 134.29, "ended"),
 ("Pathfinder + Sojourner", "USA", 1997, "Ares Vallis", 19.13, 326.78, "ended"),
 ("Spirit", "USA", 2004, "Gusev crater", -14.57, 175.47, "ended"),
 ("Opportunity", "USA", 2004, "Meridiani Planum", -1.95, 354.47, "ended"),
 ("Phoenix", "USA", 2008, "Vastitas Borealis", 68.22, 234.25, "ended"),
 ("Curiosity", "USA", 2012, "Gale crater", -4.59, 137.44, "active"),
 ("InSight", "USA", 2018, "Elysium Planitia", 4.50, 135.62, "ended"),
 ("Perseverance", "USA", 2021, "Jezero crater", 18.44, 77.45, "active"),
 ("Zhurong", "China", 2021, "Utopia Planitia", 25.07, 109.93, "ended"),
]
FUTURE = [
 ("Rosalind Franklin", "ESA", "2030", "Oxia Planum", 18.20, 335.45, "final"),
 ("Starship (lead candidate)", "SpaceX", "2027-29?", "Arcadia Planitia", 47.0, 186.0, "candidate"),
]
DRIVEN = {"Sojourner": 0.1, "Spirit": 7.73, "Opportunity": 45.16, "Curiosity": 37.0, "Perseverance": 45.2, "Zhurong": 1.9}

def gc(a, b):
    la1, lo1, la2, lo2 = map(np.radians, (a[0], a[1], b[0], b[1]))
    c = np.sin(la1)*np.sin(la2) + np.cos(la1)*np.cos(la2)*np.cos(lo2-lo1)
    return R*np.arccos(np.clip(c, -1, 1))

def shortest_open_path(pts):
    n = len(pts); D = [[gc(pts[i], pts[j]) for j in range(n)] for i in range(n)]
    INF = 1e18; dp = [[INF]*n for _ in range(1 << n)]; par = [[-1]*n for _ in range(1 << n)]
    for i in range(n): dp[1 << i][i] = 0
    for m in range(1 << n):
        for j in range(n):
            if dp[m][j] >= INF or not (m >> j) & 1: continue
            for k in range(n):
                if (m >> k) & 1: continue
                v = dp[m][j] + D[j][k]
                if v < dp[m | 1 << k][k]: dp[m | 1 << k][k] = v; par[m | 1 << k][k] = j
    full = (1 << n) - 1; end = min(range(n), key=lambda j: dp[full][j])
    order, m, j = [], full, end
    while j != -1:
        order.append(j); pj = par[m][j]; m ^= 1 << j; j = pj
    return dp[full][end], order[::-1]

def min_cap(pts):
    best = (1e18, None)
    for la in np.arange(-89, 90, 1.0):
        for lo in np.arange(0, 360, 1.0):
            r = max(gc((la, lo), p) for p in pts)
            if r < best[0]: best = (r, (la, lo))
    la0, lo0 = best[1]
    for la in np.arange(la0-1, la0+1.01, 0.1):
        for lo in np.arange(lo0-1, lo0+1.01, 0.1):
            r = max(gc((la, lo), p) for p in pts)
            if r < best[0]: best = (r, (la, lo % 360))
    return best

if __name__ == "__main__":
    P = [(p[4], p[5]) for p in PAST]
    chrono = sum(gc(P[i], P[i+1]) for i in range(len(P)-1))
    L, order = shortest_open_path(P)
    r, c = min_cap(P)
    capfrac = (1 - np.cos(r / R)) / 2
    PA = P + [(f[4], f[5]) for f in FUTURE]
    L2, order2 = shortest_open_path(PA)
    r2, c2 = min_cap(PA)
    print(f"chronological route (11 past): {chrono:,.0f} km")
    print(f"shortest single route (11 past): {L:,.0f} km  order={[PAST[i][0] for i in order]}")
    print(f"shortest route incl. 2 future: {L2:,.0f} km")
    print(f"smallest circle (11 past): radius {r:,.0f} km centre {c[0]:.1f}, {c[1]:.1f}E -> {capfrac*100:.1f}% of Mars")
    print(f"smallest circle (13 sites): radius {r2:,.0f} km centre {c2[0]:.1f}, {c2[1]:.1f}E -> {(1-np.cos(r2/R))/2*100:.1f}%")
    print(f"total driven: {sum(DRIVEN.values()):.1f} km", DRIVEN)
    print(f"Mars circumference {2*np.pi*R:,.0f} km, area {4*np.pi*R*R/1e6:.1f} M km2")
    print(f"Curiosity-Perseverance: {gc(P[7], P[9]):,.0f} km; Curiosity-InSight {gc(P[7],P[8]):,.0f} km")
