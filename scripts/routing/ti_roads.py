#!/usr/bin/env python3
"""
ti_roads.py — TES thermal inertia (Putzig & Mellon 2007) at every site and along every road.

Reads the NASA PDS product mgst_9001 (global_ti_night_2007.img + .lbl, and the
interpolation mask) directly from its PDS3 label, so no format is guessed.

  python3 ti_roads.py --img global_ti_night_2007.img --mask global_ti_msk_night_2007.img \
                      --points points.json --out ti_out

Ground classes (thermal inertia, J m^-2 K^-1 s^-1/2):
  < 100      dust-mantled, soft  -> "soft ground" warning on the road
  100 - 150  fine-grained         -> caution
  >= 150     sand / duricrust / rock -> firm
These are coarse (~3 km pixel) classes; they flag broad dusty areas, not single dunes.

Outputs in --out:
  ti_label.txt          the label fields used (check these first)
  ti_sites.csv          TI at every habitat and site (+ whether the pixel is measured or interpolated)
  ti_legs.csv           per leg: km firm / caution / soft, min and median TI, % measured
  ti_soft.geojson       soft stretches >= 20 km long (lines), for the app
  ti_preview.png        global TI map with the roads drawn on it
  ti_overlay.png/.json  0-360 E colour overlay + bounds, for the app (optional layer)
Made with AI assistance (Claude).
"""
import argparse, json, math, os, re, sys
import numpy as np

R_MARS = 3389.5  # km, mean radius (distance along roads only)

# ---------------------------------------------------------------- PDS3 label
def read_label(img_path):
    lbl = os.path.splitext(img_path)[0] + ".lbl"
    if not os.path.exists(lbl):
        lbl = os.path.splitext(img_path)[0] + ".LBL"
    txt = open(lbl, errors="replace").read()

    def get(key, default=None, cast=str):
        m = re.search(r"^\s*%s\s*=\s*(.+?)\s*$" % key, txt, re.M)
        if not m:
            return default
        v = m.group(1).split("<")[0].strip().strip('"')
        try:
            return cast(v)
        except ValueError:
            return default

    L = dict(
        label=lbl,
        lines=get("LINES", cast=int),
        samples=get("LINE_SAMPLES", cast=int),
        stype=get("SAMPLE_TYPE", ""),
        bits=get("SAMPLE_BITS", cast=int),
        scale=get("SCALING_FACTOR", 1.0, float),
        offset=get("OFFSET", 0.0, float),
        missing=get("MISSING_CONSTANT", None, str),
        res=get("MAP_RESOLUTION", None, float),            # pixels per degree
        maxlat=get("MAXIMUM_LATITUDE", 90.0, float),
        minlat=get("MINIMUM_LATITUDE", -90.0, float),
        westlon=get("WESTERNMOST_LONGITUDE", None, float),
        eastlon=get("EASTERNMOST_LONGITUDE", None, float),
        londir=get("POSITIVE_LONGITUDE_DIRECTION", "EAST").upper(),
        rec_bytes=get("RECORD_BYTES", None, int),
    )
    # ^IMAGE pointer: ("file.img", 2) or "file.img" or a record number
    m = re.search(r"^\s*\^IMAGE\s*=\s*(.+?)\s*$", txt, re.M)
    L["img_skip"] = 0
    if m:
        ptr = m.group(1)
        nums = re.findall(r"(\d+)\s*(<BYTES>)?\s*\)?\s*$", ptr)
        if nums and ("," in ptr or ptr.strip().isdigit()):
            n, isbytes = int(nums[-1][0]), bool(nums[-1][1])
            L["img_skip"] = (n - 1) if isbytes else (n - 1) * (L["rec_bytes"] or 0)
    L["raw"] = txt
    return L


def dtype_for(L):
    st, b = L["stype"].upper(), L["bits"]
    big = st.startswith("MSB") or st in ("SUN_INTEGER", "IEEE_REAL", "SUN_REAL", "MAC_INTEGER")
    e = ">" if big else "<"
    if "REAL" in st:
        return np.dtype(e + ("f4" if b == 32 else "f8"))
    if "UNSIGNED" in st:
        return np.dtype(e + {8: "u1", 16: "u2", 32: "u4"}[b])
    return np.dtype(e + {8: "i1", 16: "i2", 32: "i4"}[b])


def load(img_path, L):
    dt = dtype_for(L)
    a = np.memmap(img_path, dtype=dt, mode="r", offset=L["img_skip"],
                  shape=(L["lines"], L["samples"]))
    return a


# ---------------------------------------------------------------- geometry
class Grid:
    def __init__(self, L):
        self.n_l, self.n_s = L["lines"], L["samples"]
        self.ppd = L["res"] or self.n_s / 360.0
        self.maxlat = L["maxlat"]
        w = L["westlon"]
        if L["londir"] == "WEST":
            # sample 0 is the westernmost (largest west longitude) -> convert to east
            self.lon0_e = (360.0 - w) % 360.0 if w is not None else 0.0
        else:
            self.lon0_e = (w if w is not None else 0.0) % 360.0
        if L["westlon"] is not None and L["westlon"] < 0:   # -180..180 grids
            self.lon0_e = L["westlon"] % 360.0

    def rc(self, lat, lon_e):
        r = int(math.floor((self.maxlat - lat) * self.ppd))
        c = int(math.floor(((lon_e - self.lon0_e) % 360.0) * self.ppd))
        return min(max(r, 0), self.n_l - 1), min(max(c, 0), self.n_s - 1)


def gc_km(a, b):
    (lo1, la1), (lo2, la2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dl = math.radians(lo2 - lo1)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_MARS * math.asin(min(1.0, math.sqrt(h)))


def densify(geo, step_km=2.0):
    out = [tuple(geo[0])]
    for a, b in zip(geo[:-1], geo[1:]):
        d = gc_km(a, b)
        n = max(1, int(math.ceil(d / step_km)))
        dlon = ((b[0] - a[0] + 540) % 360) - 180
        for i in range(1, n + 1):
            t = i / n
            out.append(((a[0] + dlon * t) % 360.0, a[1] + (b[1] - a[1]) * t))
    return out


def classify(ti):
    if ti is None or not np.isfinite(ti):
        return "nodata"
    return "soft" if ti < 100 else ("caution" if ti < 150 else "firm")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--mask", default=None)
    ap.add_argument("--points", required=True)
    ap.add_argument("--out", default="ti_out")
    ap.add_argument("--soft-min-km", type=float, default=20.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    L = read_label(a.img)
    keys = ["label", "lines", "samples", "stype", "bits", "scale", "offset", "missing", "res",
            "maxlat", "minlat", "westlon", "eastlon", "londir", "rec_bytes", "img_skip"]
    with open(os.path.join(a.out, "ti_label.txt"), "w") as f:
        for k in keys:
            f.write(f"{k} = {L[k]}\n")
    print("label:", {k: L[k] for k in keys if k != "label"})

    raw = load(a.img, L)
    G = Grid(L)
    miss = None
    if L["missing"] not in (None, ""):
        try:
            miss = float(L["missing"].split()[0].replace("16#", "").rstrip("#"))
        except ValueError:
            miss = None

    def ti_at(r, c):
        v = float(raw[r, c])
        if miss is not None and v == miss:
            return float("nan")
        v = v * L["scale"] + L["offset"]
        if v <= 0 or v > 6000:      # product range is 5-5000
            return float("nan")
        return v

    msk = None
    if a.mask:
        LM = read_label(a.mask)
        msk = load(a.mask, LM)
        print("mask:", LM["stype"], LM["bits"], LM["lines"], LM["samples"])

    def measured(r, c):
        return None if msk is None else bool(msk[r, c] != 0)

    P = json.load(open(a.points))

    # --- sites
    rows = ["region,site,kind,lat,lon_e,ti,class,measured_pixel"]
    for s in P["sites"]:
        r, c = G.rc(s["lat"], s["lon"])
        v = ti_at(r, c)
        rows.append(f'{s["region"]},"{s["name"]}",{s["kind"]},{s["lat"]:.3f},{s["lon"]:.3f},'
                    f'{v:.0f},{classify(v)},{measured(r, c)}')
    open(os.path.join(a.out, "ti_sites.csv"), "w").write("\n".join(rows) + "\n")
    print("\n".join(rows))

    # --- roads
    leg_rows = ["region,leg,from,to,road_km,km_firm,km_caution,km_soft,km_nodata,ti_min,ti_median,pct_measured,soft_stretches"]
    feats = []
    tot = {"firm": 0, "caution": 0, "soft": 0, "nodata": 0}
    for rd in P["roads"]:
        pts = densify(rd["geo"], 2.0)
        vals, meas, seg = [], [], []
        for i, (lo, la) in enumerate(pts):
            r, c = G.rc(la, lo)
            vals.append(ti_at(r, c))
            meas.append(measured(r, c))
            seg.append(0.0 if i == 0 else gc_km(pts[i - 1], pts[i]))
        geo_km = sum(seg)
        k = rd["road_km"] / geo_km if geo_km > 0 else 1.0   # scale sampled length to the routed road km
        km = {"firm": 0.0, "caution": 0.0, "soft": 0.0, "nodata": 0.0}
        for v, d in zip(vals, seg):
            km[classify(v)] += d * k
        for c_ in km:
            tot[c_] += km[c_]
        # soft stretches
        n_soft = 0
        run, run_km = [], 0.0
        def flush():
            nonlocal n_soft, run, run_km
            if run and run_km >= a.soft_min_km:
                n_soft += 1
                tis = [vals[j] for j in run]
                feats.append({"type": "Feature",
                              "properties": {"region": rd["region"], "leg": rd["leg"], "from": rd["frm"], "to": rd["to"],
                                             "km": round(run_km), "ti_min": round(np.nanmin(tis)),
                                             "ti_median": round(float(np.nanmedian(tis)))},
                              "geometry": {"type": "LineString",
                                           "coordinates": [[round(pts[j][0], 3), round(pts[j][1], 3)] for j in run]}})
            run, run_km = [], 0.0
        for j, v in enumerate(vals):
            if classify(v) == "soft":
                run.append(j); run_km += seg[j] * k
            else:
                flush()
        flush()
        good = np.array([v for v in vals if np.isfinite(v)])
        mm = [m for m in meas if m is not None]
        pct_meas = (100.0 * sum(mm) / len(mm)) if mm else float("nan")
        leg_rows.append(f'{rd["region"]},{rd["leg"]},"{rd["frm"]}","{rd["to"]}",{rd["road_km"]},'
                        f'{km["firm"]:.0f},{km["caution"]:.0f},{km["soft"]:.0f},{km["nodata"]:.0f},'
                        f'{(good.min() if good.size else float("nan")):.0f},'
                        f'{(np.median(good) if good.size else float("nan")):.0f},{pct_meas:.0f},{n_soft}')
    open(os.path.join(a.out, "ti_legs.csv"), "w").write("\n".join(leg_rows) + "\n")
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(a.out, "ti_soft.geojson"), "w"))
    print("\n".join(leg_rows))
    print("TOTAL km  firm %.0f  caution %.0f  soft %.0f  nodata %.0f" % (tot["firm"], tot["caution"], tot["soft"], tot["nodata"]))
    print("soft stretches >= %.0f km: %d" % (a.soft_min_km, len(feats)))

    # --- preview + app overlay (decimated to 0.25 deg)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        step = max(1, int(round(G.ppd / 4)))
        sub = np.array(raw[::step, ::step], dtype="f4") * L["scale"] + L["offset"]
        if miss is not None:
            sub[np.array(raw[::step, ::step]) == miss] = np.nan
        sub[(sub <= 0) | (sub > 6000)] = np.nan
        # roll so column 0 is 0 E
        shift = -int(round(G.lon0_e * G.ppd / step))
        sub = np.roll(sub, shift, axis=1)
        fig, ax = plt.subplots(figsize=(16, 8))
        im = ax.imshow(sub, extent=[0, 360, L["minlat"], L["maxlat"]], cmap="viridis", vmin=30, vmax=600, aspect="auto")
        for rd in P["roads"]:
            g = np.array(rd["geo"])
            ax.plot(g[:, 0], g[:, 1], color="white", lw=2.2)
            ax.plot(g[:, 0], g[:, 1], color="black", lw=0.8)
        for f_ in feats:
            g = np.array(f_["geometry"]["coordinates"])
            ax.plot(g[:, 0], g[:, 1], color="#ff3b30", lw=3)
        for s in P["sites"]:
            ax.plot(s["lon"], s["lat"], "o", mfc="white", mec="black", ms=5)
        plt.colorbar(im, ax=ax, label="Thermal inertia (J m$^{-2}$ K$^{-1}$ s$^{-1/2}$)")
        ax.set_title("TES night thermal inertia (Putzig & Mellon 2007) — red = soft stretches (TI < 100) on the roads")
        ax.set_xlabel("East longitude"); ax.set_ylabel("Latitude")
        fig.savefig(os.path.join(a.out, "ti_preview.png"), dpi=90, bbox_inches="tight")
        plt.close(fig)
        # overlay for the app: soft = orange, caution = yellow, firm transparent
        rgba = np.zeros(sub.shape + (4,), dtype="u1")
        rgba[sub < 150] = (255, 214, 10, 90)
        rgba[sub < 100] = (255, 120, 0, 140)
        plt.imsave(os.path.join(a.out, "ti_overlay.png"), rgba)
        json.dump({"bounds": [[L["minlat"], 0], [L["maxlat"], 360]],
                   "legend": {"soft (<100)": "#ff7800", "caution (100-150)": "#ffd60a"}},
                  open(os.path.join(a.out, "ti_overlay.json"), "w"))
        print("saved preview + overlay")
    except Exception as e:  # preview is optional
        print("preview skipped:", e, file=sys.stderr)


if __name__ == "__main__":
    main()
