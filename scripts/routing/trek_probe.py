#!/usr/bin/env python3
# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
"""Probe NASA Mars Trek WMTS layers: read each layer's capabilities, then fetch real tiles.

Run on the Legion (Trek is reachable there):
    python3 trek_probe.py                 # writes trek_layers.json next to this script
Prints one line per layer: OK/FAIL, format, zoom levels, bounding box, test-tile status.
"""
import json, math, os, sys, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

BASE = "https://trek.nasa.gov/tiles/Mars/EQ/{id}/1.0.0/WMTSCapabilities.xml"
# (site, layer id) - chosen from Trek's Imagery catalogue for our stops and roads
LAYERS = [
    ("Global", "CTX_beta01_uncontrolled_5m_Caltech"),
    ("Global", "HiRISE_Global"),
    ("Global", "Mars_Viking_MDIM21_ClrMosaic_global_232m"),
    ("H1 Arcadia", "Arcadia_CTX_BlockAdj_dd"),
    ("H1 Arcadia", "Arcadia_Planitia_CTX_BlockAdj_dd"),
    ("H1 Arcadia", "Erebus_Montes_CTX_BlockAdj_dd"),
    ("H2 InSight", "InSightCTXMosaic_112917"),
    ("H2 InSight", "ESP_058005_1845_RED_spline_rect"),
    ("H2 Cerberus", "Cerberus_CTX_BlockAdj_dd"),
    ("Curiosity", "Gale_CTX_BlockAdj_dd"),
    ("Curiosity", "curiosity_ctx_mosaic"),
    ("Curiosity", "curiosity_hirise_mosaic"),
    ("Perseverance", "JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd"),
    ("Perseverance", "JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0"),
    ("Perseverance", "Jezero_CTX_BlockAdj_dd"),
    ("Spirit", "spirit_hirise_mosaic"),
    ("Spirit", "HiRISE_ColumbiaHills"),
    ("Spirit", "Gusev_CTX_BlockAdj_dd"),
    ("Opportunity", "opportunity_hirise_mosaic"),
    ("Opportunity", "HiRISE_Opportunity"),
    ("Phoenix", "phoenix_hirise_mosaic"),
    ("Pathfinder", "sojourner_hirise_mosaic"),
    ("Viking 1", "PSP_001521_2025_RED"),
    ("Viking 1", "b21_017819_2025_xn_22n048w"),
    ("Viking 2", "PSP_001501_2280_RED"),
    ("Viking 2", "b16_015887_2280_xn_48n225w"),
    ("Viking 1+2", "Viking_CTX_BlockAdj_dd"),
    ("Tianwen-3 Chryse", "Hypanis_Delta_CTX_BlockAdj_dd"),
]
UA = {"User-Agent": "MartianAutonomy-SpaceApps2026/1.0"}

def get(url, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, b"", ""
    except Exception as e:
        return 0, str(e).encode(), ""

def local(tag):
    return tag.rsplit("}", 1)[-1]

def kids(el, name):
    return [c for c in el if local(c.tag) == name]

def kid(el, name):
    k = kids(el, name)
    return k[0] if k else None

def txt(el, name):
    k = kid(el, name)
    return k.text.strip() if k is not None and k.text else None

def parse(xml):
    root = ET.fromstring(xml)
    contents = next(e for e in root.iter() if local(e.tag) == "Contents")
    layer = kid(contents, "Layer")
    out = {"formats": [f.text for f in kids(layer, "Format")]}
    bb = kid(layer, "WGS84BoundingBox")
    if bb is None:
        bb = kid(layer, "BoundingBox")
    if bb is not None:
        lo = [float(v) for v in txt(bb, "LowerCorner").split()]
        hi = [float(v) for v in txt(bb, "UpperCorner").split()]
        out["bbox"] = [lo[0], lo[1], hi[0], hi[1]]          # lon_min, lat_min, lon_max, lat_max
    ru = kid(layer, "ResourceURL")
    out["template"] = ru.get("template") if ru is not None else None
    link = kid(layer, "TileMatrixSetLink")
    out["tms"] = txt(link, "TileMatrixSet") if link is not None else None
    style = kid(layer, "Style")
    out["style"] = txt(style, "Identifier") if style is not None else "default"
    for s in kids(contents, "TileMatrixSet"):
        if out["tms"] and txt(s, "Identifier") != out["tms"]:
            continue
        out["crs"] = txt(s, "SupportedCRS")
        out["matrices"] = [{
            "id": txt(m, "Identifier"),
            "scale": float(txt(m, "ScaleDenominator")),
            "topleft": [float(v) for v in txt(m, "TopLeftCorner").split()],
            "tw": int(float(txt(m, "TileWidth"))), "th": int(float(txt(m, "TileHeight"))),       # Trek writes these as "2.0"
            "mw": int(float(txt(m, "MatrixWidth"))), "mh": int(float(txt(m, "MatrixHeight"))),
        } for m in kids(s, "TileMatrix")]
        break
    return out

def tile_url(info, lid, m, row, col):
    t = info.get("template")
    fmt = (info["formats"] or ["image/png"])[0]
    ext = "jpg" if "jpeg" in fmt or "jpg" in fmt else "png"
    if not t:
        t = f"https://trek.nasa.gov/tiles/Mars/EQ/{lid}/1.0.0/{{Style}}/{{TileMatrixSet}}/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.{ext}"
    return (t.replace("{Style}", info.get("style") or "default").replace("{TileMatrixSet}", info.get("tms") or "default028mm")
             .replace("{TileMatrix}", m["id"]).replace("{TileRow}", str(row)).replace("{TileCol}", str(col)))

def probe(item):
    site, lid = item
    rec = {"site": site, "id": lid}
    st, body, _ = get(BASE.format(id=lid))
    rec["caps_status"] = st
    if st != 200:
        rec["ok"] = False
        return rec
    try:
        info = parse(body)
    except Exception as e:
        rec.update(ok=False, error=f"parse: {e}")
        return rec
    rec.update(info)
    ms = info.get("matrices") or []
    if not ms or "bbox" not in info:
        rec["ok"] = False
        return rec
    # test tiles at the bbox centre: deepest level, a middle level, and the coarsest level
    lon_c = (info["bbox"][0] + info["bbox"][2]) / 2
    lat_c = (info["bbox"][1] + info["bbox"][3]) / 2
    rec["tests"] = []
    for m in sorted({ms[-1]["id"]: ms[-1], ms[len(ms) // 2]["id"]: ms[len(ms) // 2], ms[0]["id"]: ms[0]}.values(), key=lambda x: -x["scale"]):
        # tile span in degrees from the matrix size (Trek EQ grids start at -180,90 and cover the globe)
        sx, sy = 360.0 / m["mw"], 180.0 / m["mh"]
        tl_lon, tl_lat = m["topleft"][0], m["topleft"][1]
        if abs(tl_lat) > 90:                                     # some caps give lat,lon order
            tl_lat, tl_lon = tl_lon, tl_lat
        col = int(math.floor((lon_c - tl_lon) / sx))
        row = int(math.floor((tl_lat - lat_c) / sy))
        u = tile_url(info, lid, m, row, col)
        s2, b2, ct = get(u)
        rec["tests"].append({"level": m["id"], "row": row, "col": col, "status": s2, "bytes": len(b2), "type": ct, "url": u})
    rec["ok"] = any(t["status"] == 200 and t["bytes"] > 500 for t in rec["tests"])
    return rec

def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trek_layers.json")
    with ThreadPoolExecutor(8) as ex:
        recs = list(ex.map(probe, LAYERS))
    json.dump(recs, open(out, "w"), indent=1)
    print(f"{'site':17} {'ok':4} {'fmt':5} {'lv':>3} {'bbox lon/lat':38} tests(level:status)  id")
    for r in recs:
        fmt = (r.get("formats") or ["?"])[0].replace("image/", "")
        bb = r.get("bbox")
        bbs = f"{bb[0]:.2f},{bb[1]:.2f} .. {bb[2]:.2f},{bb[3]:.2f}" if bb else (r.get("error") or f"caps HTTP {r.get('caps_status')}")[:38]
        ts = " ".join(f"{t['level']}:{t['status']}" for t in r.get("tests", []))
        print(f"{r['site'][:17]:17} {'OK' if r.get('ok') else 'FAIL':4} {fmt:5} {len(r.get('matrices') or []):3} {bbs:38} {ts:20} {r['id']}")
    print(f"\n{sum(1 for r in recs if r.get('ok'))} of {len(recs)} layers return real tiles. Details: {out}")

if __name__ == "__main__":
    main()
