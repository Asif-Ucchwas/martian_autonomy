"""regions_plan.py - 2 habitats, 2 research regions, every site visited by road.

MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)

Model
  Region      each landing / planned site belongs to its nearest main habitat (great circle).
  Route       closed loop: habitat -> every site in the region -> habitat, shortest order
              (exact Held-Karp search on great-circle distances).
  Road        road km = straight km x 1.3 (planning value). Measured on real MOLA terrain
              InSight -> Gale: 1.08 (road_planner.py), so 1.3 is a safe upper value.
  Pace        crew 12 km/h x 8 h = 96 km per driving sol; 1 rest sol after every 6 driving sols.
  Sites       5 sols of research at each site.
  Camps       one camp at the end of every driving sol (on the road).
  Depots      robots pre-place a supply depot at least every 800 km of road
              (14 sols life support with 30 % reserve at 96 km/sol -> about 860 km).
"""
import json, math, itertools
import numpy as np
from sites import PAST, FUTURE, gc, R

ROAD_F, BEST_F = 1.3, 1.08
HOME_KM = 5.0          # a site this close to the habitat is the home site (walk, no road leg)
MEASURED = {}   # v4: every leg (incl. Gale) comes from road463.py on MOLA 463 m via legs_measured.json
# (v3 used: {frozenset(("H2", "Curiosity")): 594.5} from road_planner.py)
import os
GLOBAL = {}   # every leg on global MOLA (global_roads.py) -> {(region, frozenset(from,to)): leg}
# Soft-ground scenario (option): python3 regions_plan.py --soft ti_legs.csv
#   soft-ground km per leg from ti_roads.py (TES thermal inertia < 100); crew drives them at SOFT_KMH instead of 12 km/h.
#   This is a SCENARIO (no rover has measured speed on dust at these scales) -> written to regions_plan_soft.json.
import sys as _sys, csv as _csv
SOFT, SOFT_KMH, CREW_KMH = {}, 6.0, 12.0
# Speed sensitivity (option): python3 regions_plan.py --kmh 9.6  -> regions_plan_kmh.json (times scaled by 12 / kmh)
SPEED_SCALE = 12.0 / float(_sys.argv[_sys.argv.index("--kmh") + 1]) if "--kmh" in _sys.argv else 1.0
if "--soft" in _sys.argv:
    for _r in _csv.DictReader(open(_sys.argv[_sys.argv.index("--soft") + 1])):
        SOFT[(_r["region"], frozenset((_r["from"], _r["to"])))] = float(_r["km_soft"])
if os.path.exists("legs_measured.json"):
    for _l in json.load(open("legs_measured.json"))["legs"]:
        if _l.get("road_km"):
            GLOBAL[(_l["region"], frozenset((_l["frm"], _l["to"])))] = _l
KM_SOL, SITE_SOLS, DEPOT_KM = 96.0, 5, 800.0
# Fixed routes (v5): a region can follow a set visit order instead of the shortest closed loop, with roads driven out and back.
#   route_<hid>.json = {"order": ["HABITAT", site, ..., "HABITAT"]}; a site is researched on its first visit only.
ROUTES = {h: json.load(open(f"route_{h}.json"))["order"] for h in ("H1", "H2") if os.path.exists(f"route_{h}.json")}
DIRLEG = {}   # direction-aware measured legs: (region, from, to) -> leg (out and back differ: uphill vs downhill)
if os.path.exists("legs_measured.json"):
    for _l in json.load(open("legs_measured.json"))["legs"]:
        if _l.get("road_km"):
            DIRLEG[(_l["region"], _l["frm"], _l["to"])] = _l

HABS = {
    "H1": dict(name="Main Habitat 1 · Ice colony", place="Arcadia–Amazonis · AP-1", lat=39.809, lon=202.081,
               note="Published ice site AP-1 (Luzzi et al. 2025; SpaceX prime site), ice < 1 m deep; CTX terrain J20_052424/052490", color="#ff4f1a"),
    "H2": dict(name="Main Habitat 2 · Sun colony", place="Elysium Planitia", lat=4.49237, lon=135.60511,
               note="HiRISE-checked habitat spot, 1.2 km from InSight (DTEEC_037262_1845)", color="#ffb000"),
}
SITES = [dict(name=p[0].replace(" + Sojourner", ""), who=f"{p[1]} {p[2]}", kind="active rover" if p[6] == "active" else "landing",
              place=p[3], lat=p[4], lon=p[5]) for p in PAST]
SITES += [dict(name="Rosalind Franklin site", who="ESA 2030", kind="planned", place="Oxia Planum", lat=18.20, lon=335.45),
          dict(name="SpaceX candidate site", who="SpaceX / HiRISE 2019", kind="planned", place="Arcadia Planitia (ESP_060706)", lat=39.090, lon=189.790),
          dict(name="AP-8 ice site", who="Luzzi et al. 2025", kind="planned", place="Arcadia–Amazonis", lat=40.735, lon=201.272),
          dict(name="AP-9 ice site", who="Luzzi et al. 2025 · SpaceX prime", kind="planned", place="Arcadia–Amazonis", lat=40.016, lon=203.330),
          dict(name="Tianwen-3 zone (Chryse)", who="China ~2028", kind="planned", place="Chryse Planitia", lat=23.5, lon=315.0),
          dict(name="Tianwen-3 zone (Utopia)", who="China ~2028", kind="planned", place="Utopia Planitia", lat=23.5, lon=115.0)]


def gc_path(a, b, n=200):
    la1, lo1, la2, lo2 = map(np.radians, (a[0], a[1], b[0], b[1]))
    p1 = np.array([np.cos(la1) * np.cos(lo1), np.cos(la1) * np.sin(lo1), np.sin(la1)])
    p2 = np.array([np.cos(la2) * np.cos(lo2), np.cos(la2) * np.sin(lo2), np.sin(la2)])
    w = np.arccos(np.clip(p1 @ p2, -1, 1))
    t = np.linspace(0, 1, n)[:, None]
    q = (np.sin((1 - t) * w) * p1 + np.sin(t * w) * p2) / np.sin(w) if w > 1e-9 else np.repeat(p1[None], n, 0)
    return np.degrees(np.arcsin(q[:, 2])), np.mod(np.degrees(np.arctan2(q[:, 1], q[:, 0])), 360)


def best_loop(pts):
    """Exact shortest closed tour starting and ending at pts[0]."""
    n = len(pts)
    D = [[gc(pts[i], pts[j]) for j in range(n)] for i in range(n)]
    INF = 1e18
    dp = {(1, 0): (0.0, -1)}
    for m in range(1, 1 << n):
        if not m & 1:
            continue
        for j in range(n):
            if (m, j) not in dp:
                continue
            c, _ = dp[(m, j)]
            for k in range(1, n):
                if m >> k & 1:
                    continue
                key = (m | 1 << k, k)
                v = c + D[j][k]
                if v < dp.get(key, (INF,))[0]:
                    dp[key] = (v, j)
    full = (1 << n) - 1
    end = min(range(1, n), key=lambda j: dp[(full, j)][0] + D[j][0])
    order, m, j = [], full, end
    while j != -1:
        order.append(j)
        pj = dp[(m, j)][1]
        m ^= 1 << j
        j = pj
    order = order[::-1]
    return order + [0]


def plan_region(hid):
    h = HABS[hid]
    mine = [s for s in SITES if min(HABS, key=lambda k: gc((s["lat"], s["lon"]), (HABS[k]["lat"], HABS[k]["lon"]))) == hid]
    home = [s for s in mine if gc((s["lat"], s["lon"]), (h["lat"], h["lon"])) <= HOME_KM]
    mine = [s for s in mine if s not in home]
    pts = [(h["lat"], h["lon"])] + [(s["lat"], s["lon"]) for s in mine]
    names = ["HABITAT"] + [s["name"] for s in mine]
    if hid in ROUTES:
        order = [0 if n == "HABITAT" else names.index(n) for n in ROUTES[hid]]
        assert sorted(set(order)) == list(range(len(names))), f"{hid} route must visit every site"
    else:
        order = best_loop(pts)
    visited = set()
    sol, drive_run, road_cum, legs, camps, depots, stops = 1, 0, 0.0, [], [], [], []
    next_depot = DEPOT_KM
    stops.append(dict(stop=0, name=names[0], kind="habitat", lat=pts[0][0], lon=pts[0][1], arrive_sol=0, depart_sol=1,
                      home_sites=[f"{x['name']} ({gc((x['lat'], x['lon']), pts[0]):.1f} km, on foot)" for x in home]))
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        straight = gc(pts[a], pts[b])
        key = frozenset((names[a] if a else hid, names[b] if b else hid))
        gkey = (hid, frozenset((names[a], names[b])))
        dkey = (hid, names[a], names[b])
        if dkey in DIRLEG and hid in ROUTES:       # fixed route: use the leg measured in this direction
            gl = DIRLEG[dkey]; road, source = gl["road_km"], "MOLA 463 m"
            hrs = gl["hours_soft"] if SOFT else gl["hours"]
            dsols = max(1, math.ceil(hrs * SPEED_SCALE / 8))
        elif key in MEASURED:
            road, source = MEASURED[key], "MOLA 463 m"
            dsols = max(1, math.ceil(road / KM_SOL))
        elif gkey in GLOBAL:
            road = GLOBAL[gkey]["road_km"]
            source = "MOLA 463 m" if "hours_soft" in GLOBAL[gkey] else "MOLA global"
            if SOFT and "hours_soft" in GLOBAL[gkey]:      # v4: dust time measured along the 463 m road
                hrs = GLOBAL[gkey]["hours_soft"]
            else:
                _soft = SOFT.get((hid, frozenset((names[a], names[b]))), 0.0)
                hrs = GLOBAL[gkey]["hours"] + _soft / SOFT_KMH - _soft / CREW_KMH
            dsols = max(1, math.ceil(hrs * SPEED_SCALE / 8))
        else:
            road, source = straight * ROAD_F, "estimate x1.3"
            dsols = max(1, math.ceil(road / KM_SOL))
        measured = source != "estimate x1.3"
        la, lo = gc_path(pts[a], pts[b], 400)
        start_sol, rests = sol, 0
        for d in range(1, dsols + 1):
            km_leg = min(d * KM_SOL, road)
            frac = km_leg / road
            k = min(399, int(round(frac * 399)))
            sol += 1
            drive_run += 1
            if d < dsols:
                camps.append(dict(leg=i + 1, sol=sol, road_km=round(road_cum + km_leg), lat=round(float(la[k]), 3), lon=round(float(lo[k]), 3)))
            while road_cum + km_leg >= next_depot and next_depot < road_cum + road:
                kk = min(399, int(round((next_depot - road_cum) / road * 399)))
                depots.append(dict(id=f"{hid}-D{len(depots) + 1}", leg=i + 1, road_km=round(next_depot),
                                   lat=round(float(la[kk]), 3), lon=round(float(lo[kk]), 3)))
                next_depot += DEPOT_KM
            if drive_run == 6 and d < dsols:
                sol += 1; rests += 1; drive_run = 0
        road_cum += road
        to_home = b == 0
        first = not to_home and b not in visited
        legs.append(dict(leg=i + 1, frm=names[a], to=names[b], visit=first, straight_km=round(straight), road_km=round(road),
                         road_km_best=round(road if measured else straight * BEST_F), measured=measured, source=source, drive_sols=dsols, rest_sols=rests, camps=dsols - 1,
                         depart_sol=start_sol, arrive_sol=sol))
        if first:
            visited.add(b)
            s = mine[b - 1]
            stops.append(dict(stop=len(stops), name=s["name"], who=s["who"], kind=s["kind"], place=s["place"],
                              lat=s["lat"], lon=s["lon"], arrive_sol=sol, depart_sol=sol + SITE_SOLS,
                              km_from_habitat=round(gc(pts[0], pts[b]))))
            sol += SITE_SOLS
            if drive_run >= 6:
                drive_run = 0
    total_straight = sum(l["straight_km"] for l in legs)
    summary = dict(sites=len(mine), home_sites=[x["name"] for x in home], loop_straight_km=round(total_straight), road_km=round(road_cum),
                   road_km_best=round(sum(l["road_km_best"] for l in legs)),
                   drive_sols=sum(l["drive_sols"] for l in legs), rest_sols=sum(l["rest_sols"] for l in legs),
                   site_sols=SITE_SOLS * len(mine), total_sols=sol, camps=len(camps), depots=len(depots),
                   fits_30_sol_stay=sol <= 30, fits_500_sol_long_stay=sol <= 500)
    return dict(habitat={**h, "id": hid}, summary=summary, legs=legs, stops=stops, camps=camps, depots=depots,
                route=[[round(float(x), 3) for x in p] for i in range(len(order) - 1)
                       for p in zip(*gc_path(pts[order[i]], pts[order[i + 1]], 120))])


if __name__ == "__main__":
    out = {"model": {"road_factor": ROAD_F, "road_factor_measured": BEST_F, "km_per_sol": KM_SOL,
                     "site_sols": SITE_SOLS, "depot_km": DEPOT_KM, "note": "Made with AI assistance (Claude)"},
           "link_H1_H2_km": round(gc((HABS["H1"]["lat"], HABS["H1"]["lon"]), (HABS["H2"]["lat"], HABS["H2"]["lon"]))),
           "regions": {k: plan_region(k) for k in HABS}}
    json.dump(out, open("regions_plan_kmh.json" if SPEED_SCALE != 1.0 else ("regions_plan_soft.json" if SOFT else "regions_plan.json"), "w"), indent=1)
    for k, r in out["regions"].items():
        s = r["summary"]
        print(f"\n== {k} {r['habitat']['place']}: {s}")
        for st in r["stops"]:
            print(f"  stop {st['stop']:>2} sol {st['arrive_sol']:>4}-{st['depart_sol']:<4} {st['name']}")
        for l in r["legs"]:
            print(f"  leg {l['leg']}: {l['frm']} -> {l['to']}  {l['road_km']} km road  {l['drive_sols']} drive + {l['rest_sols']} rest sols")
    print("H1-H2 link", out["link_H1_H2_km"], "km")
