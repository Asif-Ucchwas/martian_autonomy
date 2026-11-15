"""Curiosity's real travel rate inside the DTM, from its own waypoint record.
MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
Measured, not assumed. Input: ~/msl_waypoints_in_dtm.geojson (690 waypoints).

Result (Nov 13, 2026): sols 1930 -> 5070, 20,394 m odometry, driving on 22% of sols,
median 23.5 m per driving sol (p95 58.4, max 106.1), mission pace 6.5 m per sol.
"""
import json, os, statistics as st
from collections import defaultdict

f = json.load(open(os.path.expanduser("~/msl_waypoints_in_dtm.geojson")))
P = sorted((x["properties"] for x in f["features"]), key=lambda p: (p["sol"], p["dist_total_m"]))

def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)

per_sol = defaultdict(float)
for p in P:
    per_sol[p["sol"]] += p["dist_m"]
driving = [d for d in per_sol.values() if d > 0]

s0, s1 = P[0]["sol"], P[-1]["sol"]
total = P[-1]["dist_total_m"] - P[0]["dist_total_m"]
elapsed = s1 - s0
drives = [p["dist_m"] for p in P if p["dist_m"] > 0]

print(f"Sols in DTM            : {s0} -> {s1}  ({elapsed} sols elapsed)")
print(f"Odometry in DTM        : {total:,.0f} m")
print(f"Sols with driving      : {len(driving)}  ({100*len(driving)/max(elapsed,1):.0f}% of elapsed sols)")
print(f"Overall rate           : {total/max(elapsed,1):.1f} m per sol (includes science/rest sols)")
print(f"Per driving sol        : median {st.median(driving):.1f} m, p95 {pct(driving,.95):.1f} m, max {max(driving):.1f} m")
print(f"Single drive segments  : median {st.median(drives):.1f} m, max {max(drives):.1f} m")
gaps = [b - a for a, b in zip(sorted(per_sol), sorted(per_sol)[1:]) if b - a > 30]
print(f"Gaps > 30 sols         : {len(gaps)} {gaps[:5]}  (rover may have left and re-entered the DTM)")
print("drive_type counts      :", {t: sum(1 for p in P if p['drive_type'] == t) for t in set(p['drive_type'] for p in P)})
