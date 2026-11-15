# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
"""integrate.py - put the v5 Habitat 1 route (Phoenix -> Chryse, Opportunity out-and-back) into the plan and the app.
usage: python3 integrate.py <unzipped h1v5 folder>"""
import csv, json, math, os, shutil, sys

SRC = sys.argv[1]
MG, APP, LAY = "/home/claude/marsglobal", "/home/claude/app", "/home/claude/layers"
new = json.load(open(f"{SRC}/r463_h1v5/legs_463.json"))
geo = json.load(open(f"{SRC}/r463_h1v5/legs_463.geojson"))
assert len(new) == 13 and all(r["region"] == "H1" for r in new), "expected 13 H1 legs"
order = ["HABITAT"] + [r["to"] for r in sorted(new, key=lambda r: r["leg"])]

# backups (once)
for f in (f"{MG}/legs_measured.json", f"{APP}/legs_463.geojson"):
    b = f.replace(".json", "_v4.json").replace(".geojson", "_v4.geojson")
    if not os.path.exists(b):
        shutil.copy(f, b)

# 1. measured legs: H1 replaced by the 13 direction-aware v5 legs
LMJ = json.load(open(f"{MG}/legs_measured_v4.json"))
LMJ["legs"] = [l for l in LMJ["legs"] if l["region"] != "H1"] + [dict(
    region="H1", leg=r["leg"], frm=r["frm"], to=r["to"], straight_km=r["straight_km"], road_km=r["road_km"],
    road_factor=r["road_factor"], hours=r["hours_main"], max_slope_deg=r["max_slope_deg"], hours_soft=r["hours_soft"],
    p95_slope_deg=r["p95_slope_deg"], soft_km=r["soft_km"], v3_km=r["km_v3"], pieces_failed=r["pieces_failed"]) for r in new]
LMJ["meta"] = {**LMJ.get("meta", {}), "v5": "H1 re-routed 2026-11-15: no Phoenix -> Opportunity road; new Phoenix -> Chryse road; Opportunity spur driven out and back"}
json.dump(LMJ, open(f"{MG}/legs_measured.json", "w"), indent=1)
json.dump({"order": order}, open(f"{MG}/route_H1.json", "w"), indent=1)

# 2. road shapes for the app
G = json.load(open(f"{APP}/legs_463_v4.geojson"))
G["features"] = [f for f in G["features"] if f["properties"]["region"] != "H1"] + geo["features"]
json.dump(G, open(f"{APP}/legs_463.geojson", "w"))

# 3. loose dust: ti_v5 = ti_v4 with the H1 rows / stretches replaced
T5, T4, TN = f"{LAY}/ti_v5", f"{LAY}/ti_v4", f"{SRC}/ti_h1v5"
if os.path.exists(T5):
    shutil.rmtree(T5)
shutil.copytree(T4, T5)
rows4 = list(csv.DictReader(open(f"{T4}/ti_legs.csv")))
rowsN = list(csv.DictReader(open(f"{TN}/ti_legs.csv")))
with open(f"{T5}/ti_legs.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows4[0].keys()), quoting=csv.QUOTE_NONNUMERIC)
    w.writeheader()
    for r in [r for r in rows4 if r["region"] != "H1"] + rowsN:
        w.writerow({k: r.get(k, "") for k in rows4[0]})
S4, SN = json.load(open(f"{T4}/ti_soft.geojson")), json.load(open(f"{TN}/ti_soft.geojson"))
S4["features"] = [f for f in S4["features"] if f["properties"]["region"] != "H1"] + SN["features"]
json.dump(S4, open(f"{T5}/ti_soft.geojson", "w"))

for r in sorted(new, key=lambda r: r["leg"]):
    print(f'H1-{r["leg"]:<2} {r["frm"][:24]:24} -> {r["to"][:24]:24} {r["road_km"]:7.1f} km  {r["hours_main"]:6.1f} h  max {r["max_slope_deg"]:4.1f} deg  soft {r["soft_km"]} km  failed {r["pieces_failed"]}')
print("H1 v5 total", round(sum(r["road_km"] for r in new)), "km; route:", " -> ".join(order))
