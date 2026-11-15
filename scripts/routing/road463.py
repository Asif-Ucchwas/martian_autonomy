#!/usr/bin/env python3
"""
road463.py — re-route every road on the full-resolution MGS MOLA 463 m terrain.

MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)

Why: the v3 roads were routed on 5.2 km cells, which only "see" craters of ~15 km and up.
This script follows each v3 road and searches a strip of +-BUFFER km around it on 463 m cells,
so the road bends around smaller craters and steep ground, and (optionally) around loose dust.

  python3 road463.py --dem ~/rehearsal/dtm/mola_463m.tif --points points.json \
      --ti global_ti_night_2007.img --out r463
  options: --buffer-km 40  --seg-km 300  --max-slope 12  --soft-factor 0.5  --only H1-9  --kmh 12

Model (same speed rules as road_planner.py, used for the Gale road)
  Slope     s = atan(|grad z|) per 463 m cell; cells with s > max_slope (12 deg) are blocked.
  Search    each road is cut into pieces of ~seg-km along the v3 road; each piece is searched
            in a strip of +-buffer-km around it with Dijkstra (scipy sparse graph), 16 move
            directions (8 neighbours + knight moves; a knight move needs both cells it crosses open).
            Search cost = time; speed for the search uses slope size only:
              f_route(s) = 0.5 * ( max(0.3, 1 - s/smax) + max(0.5, 1 - 0.5 s/smax) )
            Loose dust (TES thermal inertia < 100) is made costlier by --soft-factor (speed x 0.5),
            so roads bend around dust where the strip allows it.
  Time      the chosen path is then timed with the full road_planner model (direction-aware):
              uphill   f = max(0.3, 1 - g/smax)     downhill f = max(0.5, 1 - 0.5|g|/smax)
              cross-slope f *= max(0.5, 1 - 0.5 s/smax),   v = v0 * f   (v0 = 12 km/h crew)
            hours_main = no dust slowdown (the measured plan)
            hours_soft = dust driven at v x soft-factor (the half-speed scenario)
  Distances east-west cell size = pixel * cos(lat) on the sphere R = 3,396,190 m.

Outputs in --out
  legs_463.json       per leg: km, hours_main, hours_soft, max/p95 slope, climb, descent, soft km, pieces failed
  legs_463.geojson    road shapes (one point per ~1 km)
  run.txt             one line per leg (paste this back)
"""
import argparse, json, math, os, sys, time
import numpy as np
import rasterio
from rasterio.windows import Window
import pyproj
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

R_KM = 3389.5


def gc_km(a, b):  # a, b = (lon, lat)
    lo1, la1, lo2, la2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_KM * math.asin(min(1.0, math.sqrt(h)))


def densify(geo, step_km=2.0):
    """v3 road [[lon,lat],...] -> points every <= step_km with CONTINUOUS longitude (no 360 jumps)."""
    out = [[geo[0][0], geo[0][1]]]
    for b in geo[1:]:
        a = out[-1]
        dlon = ((b[0] - a[0] + 540) % 360) - 180
        bb = [a[0] + dlon, b[1]]
        d = gc_km(a, bb)
        n = max(1, int(math.ceil(d / step_km)))
        for i in range(1, n + 1):
            t = i / n
            out.append([a[0] + dlon * t, a[1] + (bb[1] - a[1]) * t])
    return out


# ---------------------------------------------------------------- DEM access (wraps at the dateline)
class DEM:
    def __init__(self, path):
        self.ds = rasterio.open(path)
        self.H, self.W = self.ds.height, self.ds.width
        T = self.ds.transform
        self.T = T
        crs = pyproj.CRS(self.ds.crs.to_wkt())
        self.inv = pyproj.Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
        self.fwd = pyproj.Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
        self.px = abs(T.a)            # metres per pixel (x)
        self.py = abs(T.e)            # metres per pixel (y)
        # longitude of column 0 centre and degrees per column, latitude of row 0 centre and deg per row
        lon0, lat0 = self.inv.transform(T.c + self.px / 2, T.f - self.py / 2)
        lon1, lat1 = self.inv.transform(T.c + self.px * 1.5, T.f - self.py * 1.5)
        self.lon0, self.dlon = lon0, lon1 - lon0
        self.lat0, self.dlat = lat0, lat1 - lat0          # dlat < 0
        self.nod = self.ds.nodata
        print(f"DEM {self.W}x{self.H}, pixel {self.px:.1f} m, col0 lon {self.lon0:.4f}, row0 lat {self.lat0:.4f}")

    def col(self, lon):   # continuous column (may be outside 0..W, handled by read)
        return (lon - self.lon0) / self.dlon

    def row(self, lat):
        return (lat - self.lat0) / self.dlat

    def lat_of_row(self, r):
        return self.lat0 + r * self.dlat

    def lon_of_col(self, c):
        return self.lon0 + c * self.dlon

    def read(self, r0, r1, c0, c1):
        """rows r0..r1-1, columns c0..c1-1 (columns may run past either edge: wrapped)."""
        r0, r1 = max(0, r0), min(self.H, r1)
        parts, c = [], c0
        while c < c1:
            cm = c % self.W
            take = min(c1 - c, self.W - cm)
            a = self.ds.read(1, window=Window(cm, r0, take, r1 - r0)).astype("float32")
            parts.append(a)
            c += take
        z = np.hstack(parts)
        if self.nod is not None:
            z[z == self.nod] = np.nan
        z[z < -1e5] = np.nan
        return z, r0


# ---------------------------------------------------------------- thermal inertia (optional)
class TI:
    def __init__(self, img):
        self.a = np.memmap(img, dtype=">i2", mode="r", shape=(3600, 7200))   # 20 ppd, lon -180..180, lat 90..-90

    def grid(self, lats, lons):
        r = np.clip(((90.0 - lats) * 20).astype(int), 0, 3599)
        c = np.clip((((lons + 180.0) % 360.0) * 20).astype(int), 0, 7199)
        v = np.asarray(self.a[np.ix_(r, c)], dtype="float32")
        v[(v <= 0) | (v > 6000)] = np.nan
        return v


# ---------------------------------------------------------------- one piece of road
HALF = [(0, 1), (1, -1), (1, 0), (1, 1), (1, -2), (1, 2), (2, -1), (2, 1)]   # 8 of the 16 directions (graph is undirected)


def dijkstra_path(cost, dx_row, py, A, B):
    H, W = cost.shape
    ok = np.isfinite(cost)
    idx = -np.ones((H, W), np.int64)
    n = int(ok.sum())
    idx[ok] = np.arange(n)
    I, J, Wt = [], [], []
    rr, cc = np.nonzero(ok)
    for dr, dc in HALF:
        r2, c2 = rr + dr, cc + dc
        m = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
        r1, c1, r2, c2 = rr[m], cc[m], r2[m], c2[m]
        m = ok[r2, c2]
        if abs(dr) + abs(dc) == 3:     # knight move: both crossed cells must be open
            if abs(dc) == 2:
                sc = np.sign(dc)
                m &= ok[r1, c1 + sc] & ok[r1 + dr, c1 + sc]
            else:
                m &= ok[r1 + 1, c1] & ok[r1 + 1, c1 + dc]
        r1, c1, r2, c2 = r1[m], c1[m], r2[m], c2[m]
        dx = 0.5 * (dx_row[r1] + dx_row[r2])
        L = np.hypot(dr * py, dc * dx)
        I.append(idx[r1, c1]); J.append(idx[r2, c2]); Wt.append(L * 0.5 * (cost[r1, c1] + cost[r2, c2]))
    G = coo_matrix((np.concatenate(Wt), (np.concatenate(I), np.concatenate(J))), shape=(n, n)).tocsr()
    a, b = idx[A], idx[B]
    dist, pred = dijkstra(G, directed=False, indices=a, return_predecessors=True)
    if not np.isfinite(dist[b]):
        return None, n
    inv_r, inv_c = rr, cc
    path, k = [], b
    while k != -9999 and k >= 0:
        path.append((int(inv_r[k]), int(inv_c[k])))
        if k == a:
            break
        k = pred[k]
    path.reverse()
    return path, n

OFFS = [(dr, dc) for dr in (-2, -1, 0, 1, 2) for dc in (-2, -1, 0, 1, 2)
        if (dr, dc) != (0, 0) and (abs(dr) <= 1 and abs(dc) <= 1 or abs(dr) + abs(dc) == 3)]   # 16 directions


def route_piece(D, ti, guide, buf_km, smax, soft_factor):
    lons = np.array([p[0] for p in guide]); lats = np.array([p[1] for p in guide])
    lat_c = float(np.mean(lats)); coslat = max(0.05, math.cos(math.radians(lat_c)))
    buf_lat = buf_km / 59.27                      # deg latitude per km on Mars ~ 1/59.27
    buf_lon = buf_lat / coslat
    r0 = int(math.floor(D.row(lats.max() + buf_lat))); r1 = int(math.ceil(D.row(lats.min() - buf_lat))) + 1
    cA, cB = D.col(lons.min() - buf_lon), D.col(lons.max() + buf_lon)
    c0, c1 = int(math.floor(min(cA, cB))), int(math.ceil(max(cA, cB))) + 1
    z, r0 = D.read(r0, r1, c0, c1)
    H, W = z.shape
    rows_lat = D.lat_of_row(np.arange(r0, r0 + H))
    cols_lon = D.lon_of_col(np.arange(c0, c0 + W))
    dx_row = D.px * np.cos(np.radians(rows_lat))            # true east-west metres per column, per row
    # slope
    zf = np.where(np.isnan(z), np.nanmean(z) if np.isfinite(np.nanmean(z)) else 0, z)
    gy, gx = np.gradient(zf)
    gy = gy / D.py; gx = gx / dx_row[:, None]
    slope = np.arctan(np.hypot(gx, gy))
    # corridor: cells within buf_km of the guide line
    seed = np.zeros((H, W), bool)
    gr = np.clip(np.round(D.row(lats) - r0).astype(int), 0, H - 1)
    gc = np.clip(np.round(D.col(lons) - c0).astype(int), 0, W - 1)
    seed[gr, gc] = True
    dist_m = ndimage.distance_transform_edt(~seed, sampling=(D.py, D.px * coslat))
    inside = dist_m <= buf_km * 1000
    # speeds
    s = np.minimum(slope / smax, 10)
    f = 0.5 * (np.maximum(0.3, 1 - s) + np.maximum(0.5, 1 - 0.5 * s))
    soft = None
    if ti is not None:
        tiv = ti.grid(rows_lat, cols_lon)
        soft = np.isfinite(tiv) & (tiv < 100)
        f = np.where(soft, f * soft_factor, f)
    cost = 1.0 / f                                      # relative time per metre
    cost[(slope > smax) | np.isnan(z) | ~inside] = np.inf
    # endpoints: snap to the nearest passable cell (within 5 km)
    def snap(r, c):
        if np.isfinite(cost[r, c]):
            return r, c
        rr, cc = np.where(np.isfinite(cost[max(0, r - 11):r + 12, max(0, c - 11):c + 12]))
        if rr.size == 0:
            return None
        k = np.argmin((rr - min(r, 11)) ** 2 + (cc - min(c, 11)) ** 2)
        return max(0, r - 11) + rr[k], max(0, c - 11) + cc[k]
    A = snap(gr[0], gc[0]); B = snap(gr[-1], gc[-1])
    if A is None or B is None:
        return None
    path, ncells = dijkstra_path(cost, dx_row, D.py, A, B)
    if path is None:
        return None
    pts = [(float(cols_lon[c]), float(rows_lat[r])) for r, c in path]
    # time the path with the direction-aware model
    v0 = 1.0
    km = h_main = h_soft = climb = desc = soft_km = 0.0
    slopes = []
    for i in range(1, len(path)):
        (ra, ca), (rb, cb) = path[i - 1], path[i]
        d = math.hypot((rb - ra) * D.py, (cb - ca) * 0.5 * (dx_row[ra] + dx_row[rb]))
        dz = float(zf[rb, cb] - zf[ra, ca])
        L = math.hypot(d, dz)
        g = math.atan2(dz, d)
        fc = max(0.3, 1 - g / smax) if g > 0 else max(0.5, 1 - 0.5 * -g / smax)
        fc *= max(0.5, 1 - 0.5 * slope[ra, ca] / smax)
        t = L / fc
        km += L / 1000
        h_main += t
        is_soft = bool(soft[rb, cb]) if soft is not None else False
        h_soft += t / soft_factor if is_soft else t
        soft_km += L / 1000 if is_soft else 0
        climb += max(dz, 0); desc += max(-dz, 0)
        slopes.append(math.degrees(slope[rb, cb]))
    return dict(pts=pts, km=km, t_main=h_main, t_soft=h_soft, climb=climb, desc=desc, soft_km=soft_km, slopes=slopes,
                cells=ncells)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dem", required=True)
    ap.add_argument("--points", required=True)
    ap.add_argument("--ti", default=None, help="global_ti_night_2007.img (optional: dust avoidance)")
    ap.add_argument("--out", default="r463")
    ap.add_argument("--buffer-km", type=float, default=40)
    ap.add_argument("--seg-km", type=float, default=300)
    ap.add_argument("--max-slope", type=float, default=12)
    ap.add_argument("--soft-factor", type=float, default=0.5)
    ap.add_argument("--kmh", type=float, default=12)
    ap.add_argument("--only", default=None, help="e.g. H1-9 or LINK-0 (comma list)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    D = DEM(os.path.expanduser(a.dem))
    ti = TI(a.ti) if a.ti else None
    smax = math.radians(a.max_slope)
    v0 = a.kmh * 1000 / 3600
    P = json.load(open(a.points))
    only = set(a.only.split(",")) if a.only else None
    res, feats, lines = [], [], []
    t_start = time.time()
    for rd in P["roads"]:
        key = f'{rd["region"]}-{rd["leg"]}'
        if only and key not in only:
            continue
        g = densify(rd["geo"], 2.0)
        # cut into pieces of ~seg-km along the guide
        cuts, acc = [0], 0.0
        for i in range(1, len(g)):
            acc += gc_km(g[i - 1], g[i])
            if acc >= a.seg_km and len(g) - i > 10:
                cuts.append(i); acc = 0.0
        cuts.append(len(g) - 1)
        allpts, km = [], 0.0
        tm = ts = cl = de = sk = 0.0
        slopes, failed = [], 0
        for i0, i1 in zip(cuts[:-1], cuts[1:]):
            piece = g[i0:i1 + 1]
            out = None
            for bk in (a.buffer_km, a.buffer_km * 2):
                out = route_piece(D, ti, piece, bk, smax, a.soft_factor)
                if out:
                    break
            if out is None:                 # keep the v3 shape for this piece, flag it
                failed += 1
                pk = sum(gc_km(piece[j - 1], piece[j]) for j in range(1, len(piece)))
                out = dict(pts=[tuple(p) for p in piece], km=pk, t_main=pk * 1000, t_soft=pk * 1000, climb=0, desc=0, soft_km=0, slopes=[])
            if allpts:
                out["pts"] = out["pts"][1:]
            allpts += out["pts"]
            km += out["km"]; tm += out["t_main"]; ts += out["t_soft"]; cl += out["climb"]; de += out["desc"]; sk += out["soft_km"]
            slopes += out["slopes"]
        straight = gc_km(g[0], g[-1])
        sl = np.array(slopes) if slopes else np.array([0.0])
        r = dict(region=rd["region"], leg=rd["leg"], frm=rd["frm"], to=rd["to"], km_v3=rd["road_km"],
                 road_km=round(km, 1), straight_km=round(straight, 1), road_factor=round(km / straight, 3) if straight else None,
                 hours_main=round(tm / v0 / 3600, 1), hours_soft=round(ts / v0 / 3600, 1),
                 max_slope_deg=round(float(sl.max()), 2), p95_slope_deg=round(float(np.percentile(sl, 95)), 2),
                 climb_m=round(cl), descent_m=round(de), soft_km=round(sk), pieces=len(cuts) - 1, pieces_failed=failed)
        res.append(r)
        step = max(1, int(round(1000 / D.py)))      # ~1 km
        coords = [[round(p[0] % 360, 4), round(p[1], 4)] for p in allpts[::step]] + [[round(allpts[-1][0] % 360, 4), round(allpts[-1][1], 4)]]
        feats.append({"type": "Feature", "properties": r, "geometry": {"type": "LineString", "coordinates": coords}})
        line = (f'{key:7s} {rd["frm"][:22]:22s} -> {rd["to"][:22]:22s} v3 {rd["road_km"]:6.0f} km | 463m {km:7.1f} km '
                f'x{r["road_factor"]} | {r["hours_main"]:6.1f} h ({r["hours_soft"]:6.1f} h soft-scn) | max {r["max_slope_deg"]:.1f} '
                f'p95 {r["p95_slope_deg"]:.1f} deg | soft {r["soft_km"]} km | pieces {r["pieces"]} failed {failed} | {time.time() - t_start:.0f}s')
        print(line, flush=True)
        lines.append(line)
        json.dump(res, open(os.path.join(a.out, "legs_463.json"), "w"), indent=1)
        json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(a.out, "legs_463.geojson"), "w"))
        open(os.path.join(a.out, "run.txt"), "w").write("\n".join(lines) + "\n")
    print("done:", len(res), "legs,", round(sum(r["road_km"] for r in res)), "km in", round(time.time() - t_start), "s")


if __name__ == "__main__":
    main()
