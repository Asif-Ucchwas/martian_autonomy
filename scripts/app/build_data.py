"""build_data.py - one JSON for the web app: regions, real roads, sol-by-sol timeline, camps, depots, site zooms.
MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)"""
import json, math
import numpy as np

R = 3389.5
P = json.load(open("/home/claude/marsglobal/regions_plan.json"))
import os
MEAS = {(l["region"], l["frm"], l["to"]): l for l in json.load(open("/home/claude/marsglobal/legs_measured.json"))["legs"]}
G = json.load(open("legs_463.geojson"))          # v4: every leg re-routed on MOLA 463 m (road463.py), +-40 km around v3
for _f in G["features"]:
    _c = _f["geometry"]["coordinates"]
    _f["geometry"]["coordinates"] = _c[::3] + ([_c[-1]] if (len(_c) - 1) % 3 else [])     # ~3 km vertex spacing for the map
    _f["properties"]["hours"] = _f["properties"]["hours_main"]
LM = {(f["properties"]["region"], f["properties"]["frm"], f["properties"]["to"]): f for f in G["features"]}
REAL_SHAPES = bool(G["features"])


def gc_coords(a, b, n=120):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    p1 = np.array([math.cos(la1) * math.cos(lo1), math.cos(la1) * math.sin(lo1), math.sin(la1)])
    p2 = np.array([math.cos(la2) * math.cos(lo2), math.cos(la2) * math.sin(lo2), math.sin(la2)])
    w = math.acos(max(-1, min(1, float(p1 @ p2))))
    out = []
    for t in np.linspace(0, 1, n):
        q = (math.sin((1 - t) * w) * p1 + math.sin(t * w) * p2) / math.sin(w)
        out.append([round(math.degrees(math.atan2(q[1], q[0])) % 360, 3), round(math.degrees(math.asin(q[2])), 3)])
    return out


def leg_feature(hid, frm, to, pa, pb):
    if (hid, frm, to) in LM:
        return LM[(hid, frm, to)]
    m = MEAS.get((hid, frm, to), {})
    return {"properties": {"max_slope_deg": m.get("max_slope_deg", 0), "climb_m": 0, "descent_m": 0},
            "geometry": {"coordinates": gc_coords(pa, pb)}}
DEPOT_KM, SITE_SOLS = 800.0, 5


def gc(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(min(1, math.sqrt(h)))


def along(coords, frac):
    seg = [gc(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]
    tot = sum(seg) or 1.0
    target, acc = frac * tot, 0.0
    for i, s in enumerate(seg):
        if acc + s >= target and s > 0:
            t = (target - acc) / s
            lo = coords[i][0] + (((coords[i + 1][0] - coords[i][0] + 180) % 360) - 180) * t
            la = coords[i][1] + (coords[i + 1][1] - coords[i][1]) * t
            return [round(lo % 360, 3), round(la, 3)]
        acc += s
    return coords[-1]


def region(hid, P=P):
    r = P["regions"][hid]
    h = r["habitat"]
    stops = {s["name"]: s for s in r["stops"][1:]}
    pos = {"HABITAT": (h["lat"], h["lon"]), **{s["name"]: (s["lat"], s["lon"]) for s in r["stops"][1:]}}
    legs, camps, depots, tl = [], [], [], []
    sol, run, road_cum, next_dep = 1, 0, 0.0, DEPOT_KM
    tl.append(dict(s=0, st="home", leg=0, lon=round(h["lon"] % 360, 3), lat=round(h["lat"], 3), km=0,
                   note="Land, set up the habitat, check the rover"))
    for l in r["legs"]:
        f = leg_feature(hid, l["frm"], l["to"], pos[l["frm"]], pos[l["to"]])
        geo = f["geometry"]["coordinates"]
        road = l["road_km"]
        legs.append(dict(leg=l["leg"], frm=l["frm"], to=l["to"], road_km=road, straight_km=l["straight_km"],
                         source=l["source"], drive_sols=l["drive_sols"], factor=round(road / l["straight_km"], 3),
                         max_slope=f["properties"]["max_slope_deg"], climb=f["properties"]["climb_m"],
                         descent=f["properties"]["descent_m"], depart=sol, geo=geo))
        n = l["drive_sols"]
        for d in range(1, n + 1):
            frac = d / n
            p = along(geo, frac)
            km = road_cum + road * frac
            last = d == n
            tl.append(dict(s=sol, st="drive", leg=l["leg"], lon=p[0], lat=p[1], km=round(km),
                           note=f"Drive {l['frm'].replace('HABITAT', 'habitat')} → {l['to'].replace('HABITAT', 'habitat')} (sol {d} of {n})"))
            while km >= next_dep and next_dep <= road_cum + road:
                q = along(geo, (next_dep - road_cum) / road)
                depots.append(dict(id=f"{hid}-D{len(depots) + 1}", leg=l["leg"], km=round(next_dep), lon=q[0], lat=q[1]))
                next_dep += DEPOT_KM
            if not last:
                camps.append(dict(n=len(camps) + 1, leg=l["leg"], sol=sol, km=round(km), lon=p[0], lat=p[1]))
            sol += 1
            run += 1
            if run == 6 and not last:
                tl.append(dict(s=sol, st="rest", leg=l["leg"], lon=p[0], lat=p[1], km=round(km), note="Rest sol at camp"))
                sol += 1
                run = 0
        road_cum += road
        legs[-1]["arrive"] = sol - 1
        if l["to"] != "HABITAT" and l.get("visit", True):      # fixed routes pass some sites a second time: no research then
            s = stops[l["to"]]
            for k in range(SITE_SOLS):
                tl.append(dict(s=sol + k, st="site", leg=l["leg"], lon=round(s["lon"] % 360, 3), lat=s["lat"], km=round(road_cum),
                               note=f"Research at {s['name']} (sol {k + 1} of {SITE_SOLS})"))
            sol += SITE_SOLS
            if run >= 6:
                run = 0
        elif l["to"] == "HABITAT":
            tl.append(dict(s=sol, st="home", leg=l["leg"], lon=round(h["lon"] % 360, 3), lat=h["lat"], km=round(road_cum),
                           note="Back at the habitat: route complete"))
    total = tl[-1]["s"]
    assert total == r["summary"]["total_sols"], (hid, total, r["summary"]["total_sols"])
    return dict(id=hid, name=h["name"], place=h["place"], lat=h["lat"], lon=h["lon"] % 360, note=h["note"],
                summary=r["summary"], stops=r["stops"][1:], legs=legs, camps=camps, depots=depots, timeline=tl)


regions = {k: region(k) for k in ("H1", "H2")}


# ---------- 30-sol short stay: best out-and-back sortie along the loop (forward or reverse), home by sol 30 ----------
def stay_plan(rg, limit=30):
    hab = dict(lon=round(rg["lon"] % 360, 3), lat=round(rg["lat"], 3))
    stops = {x["name"]: x for x in rg["stops"]}
    L_ = rg["legs"]
    n = len(L_)

    def sim(trav):
        sol, run, kmc, tl, camps, sites, arrive = 1, 0, 0.0, [], [], [], {}
        tl.append(dict(s=0, st="home", leg=0, km=0, note="Land, set up the habitat, check the rover", **hab))
        for geo, road, dn, frm, to, visit in trav:
            for d in range(1, dn + 1):
                p = along(geo, d / dn); km = kmc + road * d / dn; last = d == dn
                tl.append(dict(s=sol, st="drive", leg=0, lon=p[0], lat=p[1], km=round(km),
                               note=f"Drive {nm_(frm)} → {nm_(to)} (sol {d} of {dn})"))
                if not last:
                    camps.append(dict(n=len(camps) + 1, leg=0, sol=sol, km=round(km), lon=p[0], lat=p[1]))
                sol += 1; run += 1
                if run == 6 and not last:
                    tl.append(dict(s=sol, st="rest", leg=0, lon=p[0], lat=p[1], km=round(km), note="Rest sol at camp")); sol += 1; run = 0
            kmc += road
            if visit:
                st = stops[to]; sites.append(to); arrive[to] = sol
                for k in range(SITE_SOLS):
                    tl.append(dict(s=sol + k, st="site", leg=0, lon=round(st["lon"] % 360, 3), lat=st["lat"], km=round(kmc),
                                   note=f"Research at {to} (sol {k + 1} of {SITE_SOLS})"))
                sol += SITE_SOLS
                if run >= 6: run = 0
        tl.append(dict(s=sol, st="home", leg=0, km=round(kmc), note=f"Back at the habitat: short stay done ({len(sites)} site{'s' if len(sites) != 1 else ''})", **hab))
        return dict(end=sol, sites=sites, arrive=arrive, timeline=tl, camps=camps, km=round(kmc))

    def nm_(x): return "habitat" if x == "HABITAT" else x
    rev = lambda g: list(reversed(g))
    best = None
    for k in range(1, n):          # forward: legs 0..k-1 out, same road back
        out = [(l["geo"], l["road_km"], l["drive_sols"], l["frm"], l["to"], True) for l in L_[:k]]
        back = [(rev(l["geo"]), l["road_km"], l["drive_sols"], l["to"], l["frm"], False) for l in reversed(L_[:k])]
        r_ = sim(out + back); r_["dir"] = "forward"
        if r_["end"] <= limit and (best is None or len(r_["sites"]) > len(best["sites"]) or (len(r_["sites"]) == len(best["sites"]) and r_["end"] < best["end"])):
            best = r_
    for k in range(1, n):          # reverse: last legs, driven backwards
        seg = L_[n - k:]
        out = [(rev(l["geo"]), l["road_km"], l["drive_sols"], l["to"], l["frm"], True) for l in reversed(seg)]
        back = [(l["geo"], l["road_km"], l["drive_sols"], l["frm"], l["to"], False) for l in seg]
        r_ = sim(out + back); r_["dir"] = "reverse"
        if r_["end"] <= limit and (best is None or len(r_["sites"]) > len(best["sites"]) or (len(r_["sites"]) == len(best["sites"]) and r_["end"] < best["end"])):
            best = r_
    if best is None:
        best = sim([]); best["dir"] = "none"
    return best

stay30 = {h: stay_plan(regions[h]) for h in ("H1", "H2")}


# ---------- robots go first: depot placement before the crew lands ----------
ROBOT_KMH, ROBOT_H_SOL = 10.0, 8.0     # same robot pace as road_planner.py; 8 driving hours per sol, no rest sols
WINDOW_SOLS = 600                       # DRA 5.0: cargo one opportunity (~26 months) earlier, ~350-day cargo transit, ~180-day crew transit -> ~620 days on Mars
def depot_plan(hid):
    rg = regions[hid]
    # hours along the loop at robot pace (crew hours x 12/10), per leg, cumulative by km
    marks = [(0.0, 0.0)]
    km = h = 0.0
    for l in rg["legs"]:
        hrs = MEAS[(hid, l["frm"], l["to"])]["hours"] * 12.0 / ROBOT_KMH
        km += l["road_km"]; h += hrs; marks.append((km, h))
    tot_km, tot_h = marks[-1]
    def h_at(x):
        for (k0, h0), (k1, h1) in zip(marks[:-1], marks[1:]):
            if x <= k1:
                return h0 + (h1 - h0) * (x - k0) / max(k1 - k0, 1e-9)
        return tot_h
    deps = rg["depots"]
    best = None
    for cut in range(len(deps) + 1):        # robot A forward places deps[:cut], robot B backward places deps[cut:]
        ha = h_at(deps[cut - 1]["km"]) if cut else 0.0
        hb = (tot_h - h_at(deps[cut]["km"])) if cut < len(deps) else 0.0
        m = max(ha, hb)
        if best is None or m < best[0]:
            best = (m, cut, ha, hb)
    _, cut, ha, hb = best
    for i, d in enumerate(deps):
        if i < cut:
            d["robot"] = f"{hid}-A"; d["rsol"] = math.ceil(h_at(d["km"]) / ROBOT_H_SOL)
        else:
            d["robot"] = f"{hid}-B"; d["rsol"] = math.ceil((tot_h - h_at(d["km"])) / ROBOT_H_SOL)
    return dict(robots=[dict(id=f"{hid}-A", dir="along the loop", n=cut, km=round(deps[cut - 1]["km"]) if cut else 0, sols=math.ceil(ha / ROBOT_H_SOL)),
                        dict(id=f"{hid}-B", dir="against the loop", n=len(deps) - cut, km=round(tot_km - deps[cut]["km"]) if cut < len(deps) else 0, sols=math.ceil(hb / ROBOT_H_SOL))],
                one_robot_sols=math.ceil(h_at(deps[-1]["km"]) / ROBOT_H_SOL), depots=len(deps), loop_km=round(tot_km))
robots = {h: depot_plan(h) for h in ("H1", "H2")}
_lk = MEAS[("LINK", "Habitat 1", "Habitat 2")]
robots["LINK"] = dict(depots=int(_lk["road_km"] // 800), km=round(_lk["road_km"]), sols=math.ceil(_lk["hours"] * 12.0 / ROBOT_KMH / ROBOT_H_SOL))
robots["meta"] = dict(kmh=ROBOT_KMH, h_sol=ROBOT_H_SOL, window=WINDOW_SOLS, depot_km=DEPOT_KM)

# ---------- mission calendar (SCENARIO, not a NASA schedule) ----------
from datetime import date as _d, timedelta as _td
_MY39, _YR, _SOL = _d(2026, 9, 30), 686.97, 1.0275          # Mars Year 39 began 30 Sep 2026 (Clancy et al. 2000 count)
_ls0 = {39 + i: _MY39 + _td(days=round(i * _YR)) for i in range(0, 8)}
_opp = {2031: _d(2031, 5, 4), 2033: _d(2033, 6, 27), 2035: _d(2035, 9, 15), 2037: _d(2037, 11, 19)}   # Mars oppositions
_dep = {y: o - _td(days=85) for y, o in _opp.items()}       # Hohmann-type departure ~2-3 months before opposition (approx.)
def _sols(n): return _td(days=round(n * _SOL))
def _mission(hid, cargo_y, crew_y, my):
    cargo_land = _dep[cargo_y] + _td(days=350); crew_land = _dep[crew_y] + _td(days=180)
    loop0 = _ls0[my]; loop_n = regions[hid]["summary"]["total_sols"]; loop1 = loop0 + _sols(loop_n)
    leave = crew_land + _sols(500); home = leave + _td(days=180)
    rob = max(r["sols"] for r in robots[hid]["robots"])
    return dict(hid=hid, cargo_dep=_dep[cargo_y].isoformat(), cargo_land=cargo_land.isoformat(), robots_done=(cargo_land + _sols(rob)).isoformat(),
                crew_dep=_dep[crew_y].isoformat(), crew_land=crew_land.isoformat(), loop0=loop0.isoformat(), loop1=loop1.isoformat(),
                leave=leave.isoformat(), home=home.isoformat(), wait_sols=round((loop0 - crew_land).days / _SOL), loop_sols=loop_n,
                robot_window_sols=round((crew_land - cargo_land).days / _SOL), ls180=(loop0 + _sols(372)).isoformat(),
                spare_sols=500 - round((loop0 - crew_land).days / _SOL) - loop_n, my=my)
calendar = dict(missions=[_mission("H1", 2031, 2033, 43), _mission("H2", 2033, 2035, 44)],
                seasons=[dict(my=k, ls0=v.isoformat(), ls180=(v + _sols(372)).isoformat()) for k, v in _ls0.items()],
                windows=[dict(y=y, dep=v.isoformat()) for y, v in _dep.items()], start="2031-01-01", end="2038-01-01")
for m in calendar["missions"]:
    print("calendar", m)
for h in ("H1", "H2"):
    print("robots", h, robots[h])
print("robots LINK", robots["LINK"])


# ---------- soft ground (TES thermal inertia, Putzig & Mellon 2007; ti_roads.py) ----------
import csv
TI = next(d for d in ("/home/claude/layers/ti_v5", "/home/claude/layers/ti_v4", "/home/claude/layers/ti_out") if os.path.exists(d + "/ti_legs.csv"))
soft = None
if os.path.exists(f"{TI}/ti_legs.csv"):
    tl_ = {(r_["region"], int(r_["leg"])): r_ for r_ in csv.DictReader(open(f"{TI}/ti_legs.csv"))}
    ts_ = {r_["site"]: r_ for r_ in csv.DictReader(open(f"{TI}/ti_sites.csv"))}
    for hid, rg in regions.items():
        for l in rg["legs"]:
            t = tl_[(hid, l["leg"])]
            l.update(km_soft=int(float(t["km_soft"])), km_caution=int(float(t["km_caution"])), ti_min=int(float(t["ti_min"])), ti_med=int(float(t["ti_median"])))
        for st in rg["stops"]:
            if st["name"] in ts_: st.update(ti=int(float(ts_[st["name"]]["ti"])), ti_class=ts_[st["name"]]["class"])
        hs = next(v for k_, v in ts_.items() if v["region"] == hid and v["kind"] == "habitat")
        rg.update(ti=int(float(hs["ti"])), ti_class=hs["class"])
    lk = tl_[("LINK", 0)]
    stretches = []
    if os.path.exists(f"{TI}/ti_soft.geojson"):
        for f_ in json.load(open(f"{TI}/ti_soft.geojson"))["features"]:
            c_ = f_["geometry"]["coordinates"]
            stretches.append(dict(**f_["properties"], geo=c_[::2] + ([c_[-1]] if len(c_) % 2 == 0 else [])))
    # scenario: soft ground driven at 6 km/h (regions_plan.py --soft ti_legs.csv)
    PS = json.load(open("/home/claude/marsglobal/regions_plan_soft.json"))
    scn = {}
    for hid in ("H1", "H2"):
        rs = region(hid, PS)
        scn[hid] = dict(summary=rs["summary"], stops=[dict(name=x["name"], arrive_sol=x["arrive_sol"], depart_sol=x["depart_sol"]) for x in rs["stops"]],
                        legs=[dict(leg=x["leg"], drive_sols=x["drive_sols"], depart=x["depart"], arrive=x["arrive"]) for x in rs["legs"]],
                        camps=rs["camps"], timeline=rs["timeline"])
    _ml = MEAS[("LINK", "Habitat 1", "Habitat 2")]
    link_soft_h = _ml.get("hours_soft", _ml["hours"] + float(lk["km_soft"]) / 12)
    soft = dict(stretches=stretches, link=dict(km_soft=int(float(lk["km_soft"])), ti_min=int(float(lk["ti_min"])), sols_scn=math.ceil(link_soft_h / 8)),
                total_soft_km=round(sum(float(r_["km_soft"]) for r_ in tl_.values())),
                total_km=round(sum(float(r_["road_km"]) for r_ in tl_.values())),
                overlay=os.path.exists(f"{TI}/ti_overlay.png"), scenario=scn, kmh=6)
    print("soft ground:", soft["total_soft_km"], "of", soft["total_km"], "km;", len(stretches), "stretches; scenario",
          {h: scn[h]["summary"]["total_sols"] for h in scn})
_lm = MEAS[("LINK", "Habitat 1", "Habitat 2")]
_h1, _h2 = P["regions"]["H1"]["habitat"], P["regions"]["H2"]["habitat"]
link = next((f for f in G["features"] if f["properties"]["region"] == "LINK"), None) or {
    "properties": {"road_km": _lm["road_km"], "hours": _lm["hours"], "straight_km": _lm["straight_km"]},
    "geometry": {"coordinates": gc_coords((_h1["lat"], _h1["lon"]), (_h2["lat"], _h2["lon"]))}}

# region boundary: points equally far from both habitats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
LON = np.linspace(0, 360, 721); LAT = np.linspace(-90, 90, 361); LO, LA = np.meshgrid(LON, LAT)
def dist(la0, lo0):
    r_ = np.radians
    return np.arccos(np.clip(np.sin(r_(LA)) * np.sin(r_(la0)) + np.cos(r_(LA)) * np.cos(r_(la0)) * np.cos(r_(LO - lo0)), -1, 1))
diff = dist(regions["H1"]["lat"], regions["H1"]["lon"]) - dist(regions["H2"]["lat"], regions["H2"]["lon"])
cs = plt.contour(LON, LAT, diff, levels=[0])
boundary = [[[round(float(x), 2), round(float(y), 2)] for x, y in seg[::4]] for seg in cs.allsegs[0]]

zoom = {
    "H2": dict(site="Habitat 2 · InSight area", dtm="DTEEC_037262_1845_036761_1845_U01", px=1.01, median=1.08, p95=3.27, padq=85,
               blocked=0.9, pad=[4.51879, 135.62539], pad_note="1.01 km north of InSight (plume keep-out), max 4.4°, tilt 0.04°",
               hab=[4.49237, 135.60511], hab_note="1.97 km from pad, 1.21 km from InSight, max 1.9°",
               walk=[13.28, 29.16, 36.17], elev=-2595.0),
    "GALE": dict(site="Gale crater · Bradbury Landing", dtm="DTEEC_010573_1755_010639_1755_U01", px=1.01, median=1.80, p95=6.65, padq=86,
                 blocked=0.2, pad=[-4.57221, 137.44245], pad_note="Cargo / depot pad, 1.0 km from Curiosity's landing spot, max 3.1°",
                 hab=[-4.60089, 137.45330], hab_note="Crew camp, 1.82 km from pad, max 3.6°", walk=[7.47, 18.92, 32.99], elev=-4500.5),
    "H1": dict(site="Habitat 1 · AP-1 ice site", dtm="J20_052424_2201__J20_052490_2201", px=22.4, median=1.92, p95=4.48, padq=98,
               blocked=0.01, pad=[39.80945, 202.08106], pad_note="Landing pad at the AP-1 centre, max 1.1°, tilt 0.04°",
               hab=[39.79395, 202.07350], hab_note="1.02 km from pad, max 1.1° · near-surface ice < 1 m (Luzzi et al. 2025)",
               walk=[12.42, 48.72, 142.9], elev=-3937.4),
    "SPACEX": dict(site="SpaceX candidate site · ESP_060706", dtm="DTEEC_060706_2195_060416_2195_A01", px=1.08, median=1.59, p95=4.06, padq=97,
               blocked=0.1, pad=[39.0903, 189.79969], pad_note="Pad, max 2.3°, tilt 0.02° (HiRISE titles this image 'Candidate Landing Site for SpaceX Starship Near Arcadia Planitia')",
               hab=[39.08506, 189.81586], hab_note="1.01 km from pad, max 4.0°", walk=[12.18, 40.35, 54.95], elev=-3987.1),
}
# site zoom-ins: slope overlays from site_zoom.py (green = pad-quality ground, yellow->red = steeper than the 16.7 deg walking limit)
for _k, _d in (("H1", "zoom_ap1"), ("H2", "zoom_h2"), ("GALE", "zoom_gale"), ("SPACEX", "zoom_h1")):
    _o = json.load(open(f"/home/claude/zooms/{_d}/slope_overlay.json"))
    _sm = json.load(open(f"/home/claude/zooms/{_d}/summary.json"))
    zoom[_k].update(img=f"zoom/{_k}.png", bounds=_o["bounds_latlon"], target=_sm["target"], window_km2=_sm["window_km2"],
                    reach_km=_sm["walking"]["max_reach_km"], max_slope=_sm["slope_deg"]["max"])
road_m2 = dict(km=571.5, straight=548.2, factor=1.043, hours_out=51.4, hours_back=51.4, sols_out=8, sols_back=8,
               max_slope=10.59, p95=1.85, down=2942, up=1049, elev_insight=-2614, elev_bradbury=-4500)   # v4: road463.py (Curiosity -> Habitat 2); road_planner.py gave 594 km on 8 directions

# road corridor: points every <= 10 km along every leg and the link road (for the +-50 km sharp-imagery strip)
def densify(coords, step_km=10.0):
    out = [coords[0]]
    for a, b in zip(coords, coords[1:]):
        d = gc(a, b)
        n = max(1, int(math.ceil(d / step_km)))
        dl = ((b[0] - a[0] + 180) % 360) - 180
        for k in range(1, n + 1):
            t = k / n
            out.append([round((a[0] + dl * t) % 360, 3), round(a[1] + (b[1] - a[1]) * t, 3)])
    return out
corridor = []
for r in regions.values():
    for l in r["legs"]:
        corridor += densify(l["geo"])
corridor += densify(link["geometry"]["coordinates"])

data = dict(regions=regions, corridor=corridor, link=dict(km=link["properties"]["road_km"], hours=link["properties"]["hours"],
                                       straight=link["properties"]["straight_km"], geo=link["geometry"]["coordinates"]),
            boundary=boundary, zoom=zoom, road_m2=road_m2, soft=soft,
            climate=dict(year=668.6, seasons=[["N. spring", 194, "Ls 0–90"], ["N. summer", 178, "Ls 90–180"], ["N. autumn", 142, "Ls 180–270"], ["N. winter", 154, "Ls 270–360"]],
                         calm=372,
                         h2=dict(src="InSight, 1.2 km from the habitat (measured 2018–2022)", high=-17, low=-95, gust=17, p_lo=700, p_hi=780,
                                 power0=5000, power1=500, power_end=285),
                         h1=dict(src="Viking Lander 2, Utopia Planitia 47.6°N — nearest measured northern-plains weather (1976–1980)", low=-120, p_lo=730, p_hi=1080),
                         storm2018=dict(ls=185, tau=8.5)),
            speed96={h: json.load(open("/home/claude/marsglobal/regions_plan_kmh.json"))["regions"][h]["summary"]["total_sols"] for h in ("H1", "H2")},
            stay30=stay30, robots=robots,
            calendar=calendar,
            rad=dict(surface=0.64, surface_err=0.12, cruise=1.84, cruise_days=180, sol_days=1.0275, limit=600, spe_limit=250, surface_design=0.8),
            real_shapes=REAL_SHAPES, meta=dict(made="Made with AI assistance (Claude)", team="MartianAutonomy", author="Md Asifuzzaman"))
json.dump(data, open("app_data.json", "w"), separators=(",", ":"))
print("app_data.json", os.path.getsize("app_data.json") // 1024, "KB", "real road shapes" if REAL_SHAPES else "PLACEHOLDER great-circle shapes")
for k, r in regions.items():
    print(k, r["summary"]["total_sols"], len(r["timeline"]), "timeline entries", len(r["camps"]), "camps", len(r["depots"]), "depots")
