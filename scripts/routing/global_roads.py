#!/usr/bin/env python3
"""global_roads.py - route EVERY leg of both research regions on real global MOLA terrain.

MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
Terrain: MGS MOLA global DEM (NASA/USGS), downsampled to 4096 x 2048 (~5.2 km pixels).

Usage
  python3 global_roads.py mola_global_4k.tif regions_plan.json            # default: 2x coarser (~10 km cells), fast
  python3 global_roads.py mola_global_4k.tif regions_plan.json --down 1   # full 5 km cells, slower
  output: global_roads/legs_measured.json, legs.geojson, global_roads.png

Model (same as road_planner.py, scaled to a global grid)
  Grid    equirectangular, wraps around in longitude. Cell size: north-south R*dlat,
          east-west R*dlon*cos(lat).
  Slope   per cell from neighbouring cells. At ~10 km cells the terrain is heavily smoothed,
          so the block limit is lower than on local maps: default 6 deg (catches canyon walls,
          volcano flanks, big crater rims). Local driving still needs HiRISE/CTX checks.
  Speed   crew 12 km/h, slower uphill / downhill / on side slopes (factors as road_planner.py).
  Search  A* on travel time, heuristic = great-circle distance / top speed.
  Result  road km, travel hours, road factor (= road / straight) for every leg.
"""
import argparse, heapq, json, math, os
import numpy as np
import rasterio, pyproj

R_GC = 3389.5e3


def gc_m(la1, lo1, la2, lo2):
    la1, lo1, la2, lo2 = map(math.radians, (la1, lo1, la2, lo2))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_GC * math.asin(min(1.0, math.sqrt(h)))


def load(path, down):
    with rasterio.open(path) as d:
        z = d.read(1).astype("float64")
        T = d.transform
        Rm = pyproj.CRS(d.crs.to_wkt()).ellipsoid.semi_major_metre
        nod = d.nodata
    if nod is not None:
        z[z == nod] = np.nan
    if down > 1:
        H, W = z.shape[0] // down, z.shape[1] // down
        z = np.nanmean(z[:H * down, :W * down].reshape(H, down, W, down), axis=(1, 3))
        T = T * T.scale(down, down)
    H, W = z.shape
    lon = np.degrees((T.c + (np.arange(W) + 0.5) * T.a) / Rm)
    lat = np.degrees((T.f + (np.arange(H) + 0.5) * T.e) / Rm)
    return z, lat, lon, Rm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dem"); ap.add_argument("plan")
    ap.add_argument("--down", type=int, default=2)
    ap.add_argument("--max-slope", type=float, default=6.0)
    ap.add_argument("--kmh", type=float, default=12.0)
    ap.add_argument("--out", default="global_roads")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    z, lat, lon, Rm = load(a.dem, a.down)
    H, W = z.shape
    zf = np.where(np.isfinite(z), z, np.nanmean(z))
    dlat = abs(lat[1] - lat[0]); dlon = abs(lon[1] - lon[0])
    dy = Rm * math.radians(dlat)
    dx = Rm * math.radians(dlon) * np.cos(np.radians(lat))           # per row
    dx = np.maximum(dx, dy * 0.05)
    gy = (np.roll(zf, -1, 0) - np.roll(zf, 1, 0)) / (2 * dy); gy[0] = gy[-1] = 0
    gx = (np.roll(zf, -1, 1) - np.roll(zf, 1, 1)) / (2 * dx[:, None])
    slope = np.arctan(np.hypot(gx, gy))
    smax = math.radians(a.max_slope)
    blocked = ~np.isfinite(z) | (slope > smax) | (np.abs(lat)[:, None] > 80)
    v0 = a.kmh / 3.6
    print(f"grid {W} x {H}, cell ~{dy/1000:.1f} km, blocked {blocked.mean()*100:.1f} % (slope > {a.max_slope} deg or |lat| > 80)")

    def rc(la, lo):
        r = int(np.argmin(np.abs(lat - la)))
        c = int(np.argmin(np.abs(((lon - lo + 180) % 360) - 180)))
        return r, c

    # 16 directions (8 neighbours + knight moves): grid paths stay within ~3 % of true distance
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1),
          (-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (1, -2), (-1, 2), (1, 2)]

    def step(r, c, r2, c2, dr=None, dc=None):
        if dr is None:
            dr = r2 - r
            dc = ((c2 - c + W // 2) % W) - W // 2
        d = math.hypot(dr * dy, dc * 0.5 * (dx[r] + dx[r2]))
        dz = zf[r2, c2] - zf[r, c]
        g = math.atan2(dz, d)
        f = max(0.3, 1 - g / smax) if g > 0 else max(0.5, 1 - 0.5 * -g / smax)
        f *= max(0.5, 1 - 0.5 * slope[r, c] / smax)
        L = math.hypot(d, dz)
        return L, L / (v0 * f), dz

    def route(p, q):
        s, g = rc(*p), rc(*q)
        blk = blocked.copy(); blk[s] = blk[g] = False
        cost = {s: 0.0}; prev = {s: None}
        gla, glo = lat[g[0]], lon[g[1]]
        pq = [(gc_m(lat[s[0]], lon[s[1]], gla, glo) / v0, 0.0, s)]
        n = 0
        while pq:
            f, t, u = heapq.heappop(pq)
            if t > cost.get(u, 1e30):
                continue
            n += 1
            if u == g:
                break
            r, c = u
            for drr, dcc in nb:
                r2 = r + drr
                if not 0 <= r2 < H:
                    continue
                c2 = (c + dcc) % W
                if blk[r2, c2]:
                    continue
                if abs(drr) == 2 or abs(dcc) == 2:      # knight move: both cells it passes must be open
                    m1 = (r + (drr // 2 if abs(drr) == 2 else 0), (c + (dcc // 2 if abs(dcc) == 2 else 0)) % W)
                    m2 = (r + (drr // 2 if abs(drr) == 2 else drr), (c + (dcc // 2 if abs(dcc) == 2 else dcc)) % W)
                    if not (0 <= m1[0] < H and 0 <= m2[0] < H) or blk[m1] or blk[m2]:
                        continue
                _, dt, _ = step(r, c, r2, c2, drr, dcc)
                nt = t + dt
                if nt < cost.get((r2, c2), 1e30):
                    cost[(r2, c2)] = nt; prev[(r2, c2)] = u
                    heapq.heappush(pq, (nt + gc_m(lat[r2], lon[c2], gla, glo) / v0, nt, (r2, c2)))
        if g not in prev:
            return None
        path = []; u = g
        while u is not None:
            path.append(u); u = prev[u]
        path.reverse()
        km = hrs = up = dn = 0.0; smx = 0.0
        for (r, c), (r2, c2) in zip(path, path[1:]):
            L, dt, dz = step(r, c, r2, c2)
            km += L / 1000; hrs += dt / 3600; up += max(dz, 0); dn += max(-dz, 0)
            smx = max(smx, math.degrees(slope[r2, c2]))
        return dict(road_km=round(km, 1), hours=round(hrs, 1), climb_m=round(up), descent_m=round(dn),
                    max_slope_deg=round(smx, 2), cells=n,
                    coords=[[round(float(lon[c]) % 360, 3), round(float(lat[r]), 3)] for r, c in path[::2] + [path[-1]]])

    plan = json.load(open(a.plan))
    out, feats = [], []
    jobs = []
    for hid, reg in plan["regions"].items():
        pts = {"HABITAT": (reg["habitat"]["lat"], reg["habitat"]["lon"])}
        for st in reg["stops"][1:]:
            pts[st["name"]] = (st["lat"], st["lon"])
        for l in reg["legs"]:
            jobs.append((hid, l["leg"], l["frm"], l["to"], pts[l["frm"]], pts[l["to"]]))
    h1 = plan["regions"]["H1"]["habitat"]; h2 = plan["regions"]["H2"]["habitat"]
    jobs.append(("LINK", 0, "Habitat 1", "Habitat 2", (h1["lat"], h1["lon"]), (h2["lat"], h2["lon"])))
    for hid, leg, frm, to, p, q in jobs:
        straight = gc_m(*p, *q) / 1000
        res = route(p, q)
        if res is None:
            print(f"{hid} leg {leg}: {frm} -> {to}: NO ROUTE under {a.max_slope} deg (try --max-slope 8)")
            out.append(dict(region=hid, leg=leg, frm=frm, to=to, straight_km=round(straight, 1), road_km=None)); continue
        fac = res["road_km"] / straight if straight > 0 else 1
        print(f"{hid} leg {leg}: {frm} -> {to}: straight {straight:,.0f} km, road {res['road_km']:,.0f} km "
              f"(x{fac:.2f}), {res['hours']:.0f} h driving, max slope {res['max_slope_deg']} deg")
        coords = res.pop("coords")
        out.append(dict(region=hid, leg=leg, frm=frm, to=to, straight_km=round(straight, 1), road_factor=round(fac, 3), **res))
        feats.append({"type": "Feature", "properties": out[-1], "geometry": {"type": "LineString", "coordinates": coords}})

    meta = dict(dem=os.path.basename(a.dem), cell_km=round(dy / 1000, 2), max_slope_deg=a.max_slope, kmh=a.kmh,
                data="MGS MOLA global DEM (NASA/USGS)", note="Made with AI assistance (Claude)")
    json.dump(dict(meta=meta, legs=out), open(f"{a.out}/legs_measured.json", "w"), indent=1)
    json.dump({"type": "FeatureCollection", "features": feats}, open(f"{a.out}/legs.geojson", "w"))

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    hs = LightSource(azdeg=315, altdeg=35).hillshade(zf, dx=dy, dy=dy, vert_exag=30)
    sh = int(np.argmin(np.abs(lon - 0)))
    hs = np.roll(hs, -sh, axis=1)
    fig, ax = plt.subplots(figsize=(16, 8.4))
    ax.imshow(hs, cmap="copper", extent=[0, 360, -90, 90], aspect="auto")
    bl = np.roll(np.where(blocked, 1.0, np.nan), -sh, axis=1)
    ax.imshow(bl, cmap="Greys", vmin=0, vmax=1.3, alpha=0.5, extent=[0, 360, -90, 90], aspect="auto")
    col = {"H1": "#ff4f1a", "H2": "#ffcc33", "LINK": "#ffffff"}
    for f in feats:
        c = np.array(f["geometry"]["coordinates"])
        br = np.where(np.abs(np.diff(c[:, 0])) > 180)[0] + 1
        for seg in np.split(c, br):
            ax.plot(seg[:, 0], seg[:, 1], color=col[f["properties"]["region"]], lw=2.2 if f["properties"]["region"] != "LINK" else 1.4,
                    ls="-" if f["properties"]["region"] != "LINK" else "--")
    for hid, reg in plan["regions"].items():
        for st in reg["stops"]:
            ax.plot(st["lon"] % 360, st["lat"], "o" if st["stop"] else "^", ms=6 if st["stop"] else 12, mfc="white", mec="k")
    tot = {k: sum(l["road_km"] or 0 for l in out if l["region"] == k) for k in ("H1", "H2")}
    ax.set_title(f"Every leg routed on real MOLA terrain ({dy/1000:.0f} km cells, grey = blocked > {a.max_slope} deg)  ·  "
                 f"H1 loop {tot['H1']:,.0f} km  ·  H2 loop {tot['H2']:,.0f} km", fontsize=11)
    ax.set_xlabel("Longitude (deg E)"); ax.set_ylabel("Latitude (deg N)")
    fig.text(0.01, 0.01, "Data: MGS MOLA global DEM (NASA/USGS) · Made with AI assistance (Claude)", fontsize=8)
    fig.savefig(f"{a.out}/global_roads.png", dpi=110, bbox_inches="tight")
    print(f"\nWrote {a.out}/legs_measured.json legs.geojson global_roads.png")


if __name__ == "__main__":
    main()
