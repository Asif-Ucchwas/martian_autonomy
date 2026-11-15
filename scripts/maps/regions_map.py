# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
from sites import R

P = json.load(open("regions_plan.json"))
LM = json.load(open("legs_measured.json"))["legs"]
APP = json.load(open("/home/claude/app/app_data.json"))     # real routed road shapes + camps/depots along them
REG = P["regions"]
halo = [pe.withStroke(linewidth=3, foreground="white")]
COL = {"H1": "#ff4f1a", "H2": "#e09a00"}
DARK = {"H1": "#a32a00", "H2": "#7a5200"}
W_, H_ = 22, 13.5


def pw(ax, la, lo, **k):
    la, lo = np.asarray(la), np.mod(np.asarray(lo), 360)
    b = np.where(np.abs(np.diff(lo)) > 180)[0] + 1
    for a_, o_ in zip(np.split(la, b), np.split(lo, b)):
        ax.plot(o_, a_, **k)


def header(fig, sheet, title):
    hd = fig.add_axes([0, 12.85 / H_, 1, 0.65 / H_]); hd.axis("off")
    hd.add_patch(Rectangle((0, 0), 1, 1, color="#d6d6d6", transform=hd.transAxes))
    hd.text(0.012, 0.5, "MARTIAN AUTONOMY", fontsize=18, weight="bold", va="center")
    hd.text(0.19, 0.5, "Team MartianAutonomy  ·  NASA Space Apps Challenge 2026, Houston", fontsize=11, va="center", color="#333")
    hd.text(0.988, 0.5, f"Martian Map Series  ·  {sheet}", fontsize=12, va="center", ha="right", style="italic", color="#333")
    fig.text(0.5, 0.35 / H_, f"{title}  ·  Md Asifuzzaman · Team MartianAutonomy · 2026  ·  Made with AI assistance (Claude)",
             ha="center", fontsize=12, weight="bold")


def house(ax, x, y, s, c):
    ax.add_patch(Polygon([(x - s, y - s * .9), (x + s, y - s * .9), (x + s, y + s * .2), (x, y + s * 1.1), (x - s, y + s * .2)],
                         closed=True, fc=c, ec="#111", lw=2, zorder=12))


def basemap(ax):
    img = plt.imread("/home/claude/app/site/basemap.jpg")   # MOLA shaded relief, already 0..360E
    ax.imshow(img, extent=[0, 360, -90, 90], aspect="auto")
    LON = np.linspace(0, 360, 720); LAT = np.linspace(90, -90, 360); LO, LA = np.meshgrid(LON, LAT)
    def d(la0, lo0):
        r = np.radians
        c = np.sin(r(LA)) * np.sin(r(la0)) + np.cos(r(LA)) * np.cos(r(la0)) * np.cos(r(LO - lo0))
        return np.arccos(np.clip(c, -1, 1))
    h1, h2 = REG["H1"]["habitat"], REG["H2"]["habitat"]
    near1 = d(h1["lat"], h1["lon"]) < d(h2["lat"], h2["lon"])
    tint = np.zeros((360, 720, 4)); tint[near1] = (1, .31, .1, .18); tint[~near1] = (1, .69, 0, .16)
    ax.imshow(tint, extent=[0, 360, -90, 90], aspect="auto", zorder=1)
    ax.contour(LON, LAT, near1.astype(float), levels=[.5], colors="white", linewidths=1.6, linestyles="--", zorder=2)
    ax.set_xlim(0, 360); ax.set_ylim(-90, 90)
    ax.set_xticks(range(0, 361, 30)); ax.set_yticks(range(-90, 91, 30))
    ax.set_xticklabels([f"{t}°E" for t in range(0, 361, 30)], fontsize=9)
    ax.set_yticklabels([f"{abs(t)}°{'S' if t < 0 else ('N' if t > 0 else '')}" for t in range(-90, 91, 30)], fontsize=9)


def draw_region(ax, hid, big=False):
    r, c = REG[hid], COL[hid]
    A = APP["regions"][hid]
    for st in (APP.get("soft") or {}).get("stretches", []):          # loose dust (TES thermal inertia < 100)
        if st["region"] in (hid, "LINK"):
            g = np.array(st["geo"])
            pw(ax, g[:, 1], g[:, 0], color="#c13cff", lw=9 if big else 7, alpha=.45, zorder=3.5, solid_capstyle="butt")
    for l in A["legs"]:
        g = np.array(l["geo"])
        pw(ax, g[:, 1], g[:, 0], color="white", lw=5.5 if big else 4.5, zorder=4, solid_capstyle="round")
        pw(ax, g[:, 1], g[:, 0], color=c, lw=3.2 if big else 2.6, zorder=5)
    cm = A["camps"]
    ax.scatter(np.mod([x["lon"] for x in cm], 360), [x["lat"] for x in cm], s=9 if big else 5, c="white", ec=DARK[hid], lw=.6, zorder=6)
    dp = A["depots"]
    ax.scatter(np.mod([x["lon"] for x in dp], 360), [x["lat"] for x in dp], s=46 if big else 30, marker="s", c="#2b6cb0", ec="white", lw=1, zorder=7)
    for st in r["stops"][1:]:
        x, y = st["lon"] % 360, st["lat"]
        mk = "*" if st["kind"] == "active rover" else ("D" if st["kind"] == "planned" else "o")
        ax.plot(x, y, marker=mk, ms=17 if mk == "*" else 13, mfc="white", mec=DARK[hid], mew=2.2, zorder=9)
        ax.text(x, y, str(st["stop"]), fontsize=7.5, weight="bold", ha="center", va="center", color=DARK[hid], zorder=10)
        if big:
            ob = {"Tianwen-3 zone (Chryse)": (-30, 34), "Viking 1": (-34, -26), "Pathfinder": (8, 40),
                  "Rosalind Franklin site": (-10, -40), "SpaceX candidate site": (-14, 30), "AP-8 ice site": (-30, 34), "AP-9 ice site": (30, -30), "Opportunity": (-14, -24),
                  "Tianwen-3 zone (Utopia)": (16, -26), "Zhurong": (-14, 22), "Perseverance": (-14, 18)}.get(st["name"], (9, 6))
            ax.annotate(f"{st['stop']} {st['name']}\nsol {st['arrive_sol']}–{st['depart_sol']}", (x, y), xytext=ob,
                        textcoords="offset points", fontsize=8.6, weight="bold", color="#111", path_effects=halo, zorder=11,
                        ha="left" if ob[0] >= 0 else "right", va="center",
                        arrowprops=dict(arrowstyle="-", color="#333", lw=.8) if abs(ob[0]) + abs(ob[1]) > 30 else None)
        else:
            off = {"Tianwen-3 zone (Chryse)": (-10, 13), "Viking 1": (-10, -12), "Pathfinder": (0, 14),
                   "Rosalind Franklin site": (10, -13), "SpaceX candidate site": (-12, -12), "AP-8 ice site": (8, 12), "AP-9 ice site": (10, -12), "Tianwen-3 zone (Utopia)": (10, -12),
                   "Zhurong": (-8, 11), "Opportunity": (-10, -12), "Perseverance": (-8, 10)}.get(st["name"], (8, 5))
            ax.annotate(st["name"], (x, y), xytext=off, textcoords="offset points", fontsize=8, weight="bold",
                        ha="left" if off[0] >= 0 else "right", color="#111", path_effects=halo, zorder=11)
    h = r["habitat"]
    house(ax, h["lon"] % 360, h["lat"], 3.0, c)


# ---------- sheet 7: both regions ----------
pdf = PdfPages("Mars_Research_Regions_Routes.pdf")
fig = plt.figure(figsize=(W_, H_), facecolor="white")
header(fig, "Sheet 7", "Two Habitats, Two Research Regions, Every Site by Road")
ax = fig.add_axes([0.6 / W_, 4.1 / H_, 14.6 / W_, 7.5 / H_])
basemap(ax)
h1, h2 = REG["H1"]["habitat"], REG["H2"]["habitat"]
from regions_plan import gc_path
_lk_geo = np.array(APP["link"]["geo"]); la, lo = _lk_geo[:, 1], _lk_geo[:, 0]
pw(ax, la, lo, color="#f2f2f2", lw=2.4, zorder=4)
mid = len(la) // 2
_lk = next(l for l in LM if l["region"] == "LINK")
ax.annotate(f"link road H1–H2\n{_lk['road_km']:,.0f} km · {_lk['hours'] / 8:.0f} driving sols", (lo[mid], la[mid]), xytext=(46, -6), textcoords="offset points",
            fontsize=8.5, ha="center", weight="bold", path_effects=halo, zorder=11)
for hid in ("H1", "H2"):
    draw_region(ax, hid)
for hid, dxy in (("H1", (30, 40)), ("H2", (-22, -40))):
    h = REG[hid]["habitat"]; s = REG[hid]["summary"]
    ax.annotate(f"{h['name']}\n{s['sites']} sites · {s['road_km']:,} km · {s['total_sols']} sols",
                (h["lon"] % 360, h["lat"]), xytext=dxy, textcoords="offset points", fontsize=10.5, weight="bold", color="white",
                ha="left" if dxy[0] > 0 else "right", va="center", zorder=13,
                bbox=dict(boxstyle="round,pad=0.35", fc=COL[hid], ec="#111", lw=1.2), arrowprops=dict(arrowstyle="-", color="#111", lw=1.2))
ax.set_title("Each habitat explores every landing site in its half of Mars — one road route per region", fontsize=15, weight="bold", loc="left", pad=8)

rp = fig.add_axes([15.6 / W_, 1.5 / H_, 6.1 / W_, 11.0 / H_]); rp.axis("off"); rp.set_xlim(0, 10); rp.set_ylim(0, 26)
y = 25.6
for hid in ("H1", "H2"):
    r = REG[hid]; s = r["summary"]; c = COL[hid]
    rp.add_patch(Rectangle((0, y - .9), 10, .9, fc=c, ec="none"))
    rp.text(.2, y - .45, f"{r['habitat']['name']}", fontsize=11, weight="bold", color="white", va="center")
    rp.text(.2, y - 1.4, f"{r['habitat']['place']} · {r['habitat']['lat']:.2f}°N {r['habitat']['lon']:.2f}°E", fontsize=8.6, style="italic", va="center")
    if s["home_sites"]:
        rp.text(.2, y - 1.95, f"Home site (on foot): {', '.join(s['home_sites'])}", fontsize=8.6, va="center", color="#0b7a3b", weight="bold")
    yy = y - 2.55
    rp.text(.2, yy, "stop  site", fontsize=8, weight="bold", color="#555", va="center")
    rp.text(7.1, yy, "arrive", fontsize=8, weight="bold", color="#555", va="center", ha="right")
    rp.text(9.9, yy, "from hab.", fontsize=8, weight="bold", color="#555", va="center", ha="right")
    for st in r["stops"][1:]:
        yy -= .5
        rp.text(.35, yy, f"{st['stop']:>2}", fontsize=8.6, weight="bold", color=DARK[hid], va="center")
        rp.text(1.0, yy, st["name"], fontsize=8.6, va="center")
        rp.text(7.1, yy, f"sol {st['arrive_sol']}", fontsize=8.6, va="center", ha="right")
        rp.text(9.9, yy, f"{st['km_from_habitat']:,} km", fontsize=8.6, va="center", ha="right", color=DARK[hid])
    yy -= .65
    rp.text(.2, yy, f"Route {s['road_km']:,} km of road, measured on MOLA terrain", fontsize=8.6, va="center", weight="bold")
    rp.text(.2, yy - .5, f"{s['drive_sols']} driving + {s['rest_sols']} rest + {s['site_sols']} site sols = {s['total_sols']} sols", fontsize=8.6, va="center")
    rp.text(.2, yy - 1.0, f"{s['camps']} road camps · {s['depots']} supply depots (robots, every 800 km)", fontsize=8.6, va="center")
    y = yy - 1.75
rp.add_patch(Rectangle((0, y - 2.9), 10, 2.9, fc="#fff3cd", ec="#c9a227", lw=1.2))
rp.text(.2, y - .45, "What this means for the 2 crew", fontsize=9.5, weight="bold", va="center")
for j, t in enumerate([f"A full region route takes {min(REG[k]['summary']['total_sols'] for k in REG)}–{max(REG[k]['summary']['total_sols'] for k in REG)} sols.", "It does NOT fit a 30-sol short stay.",
                       "It fits NASA's long-stay option (~500 sols).", "Short stay: home site + the nearest site only."]):
    rp.text(.3, y - 1.0 - j * .45, "• " + t, fontsize=8.6, va="center")

lg = fig.add_axes([0.6 / W_, 2.3 / H_, 14.6 / W_, 1.3 / H_]); lg.axis("off"); lg.set_xlim(0, 14.6); lg.set_ylim(0, 1.4)
items = [("h1", "Main habitat 1 (ice) + its route"), ("h2", "Main habitat 2 (sun) + its loop"), ("star", "Active rover site"),
         ("o", "Past landing site"), ("D", "Planned / future site"), ("camp", "Road camp (end of each sol)"),
         ("dep", "Supply depot (≤800 km apart)"), ("link", "Link road between habitats"), ("dust", "Soft ground (loose dust)"), ("bnd", "Region boundary (nearest habitat)")]
for k, (sym, t) in enumerate(items):
    x = .2 + (k % 5) * 2.9; yy = 1.0 - (k // 5) * .6
    if sym in ("h1", "h2"):
        lg.add_patch(Polygon([(x, yy - .18), (x + .36, yy - .18), (x + .36, yy + .05), (x + .18, yy + .22), (x, yy + .05)],
                             fc=COL["H1" if sym == "h1" else "H2"], ec="#111"))
    elif sym == "star": lg.plot(x + .18, yy, "*", ms=15, mfc="white", mec="#333", mew=2)
    elif sym in ("o", "D"): lg.plot(x + .18, yy, sym, ms=10, mfc="white", mec="#333", mew=2)
    elif sym == "camp": lg.scatter([x + .18], [yy], s=14, c="white", ec="#333")
    elif sym == "dep": lg.scatter([x + .18], [yy], s=40, marker="s", c="#2b6cb0", ec="white")
    elif sym == "link": lg.plot([x, x + .4], [yy, yy], color="#555", lw=3)
    elif sym == "dust": lg.plot([x, x + .4], [yy, yy], color="#c13cff", lw=8, alpha=.45, solid_capstyle="butt")
    else: lg.plot([x, x + .4], [yy, yy], color="#999", lw=1.6, ls="--")
    lg.text(x + .55, yy, t, fontsize=9.5, va="center")
note = ("Regions: every landing site and planned site goes to its nearest main habitat. Visit order: Habitat 2 = exact shortest closed tour (Held-Karp); Habitat 1 = set route, Opportunity branch out and back (v5).\n"
        "Every leg routed on real NASA MOLA terrain at full 463 m resolution (ground over 12° blocked, loose dust avoided where possible; guided by a 5.2 km global pass). Road factors 1.01–1.06. Driving sols = routed travel time ÷ 8 h (crew 12 km/h, slower on slopes); 1 rest sol per 6 driving sols; 5 sols per site.\n"
        "Habitat 1 = published ice site AP-1 (Luzzi et al. 2025, JGR Planets), checked on CTX terrain; Habitat 2 checked on HiRISE (pad ≤ 15°, tilt ≤ 5° over 200 m, 1 km plume rule). AP sites = HiRISE image centres. Basemap: NASA MGS MOLA shaded relief. Tianwen-3 zones approximate (final site due end of 2026).")
fig.text(0.6 / W_, 1.95 / H_, note, fontsize=8, color="#555", va="top")
pdf.savefig(fig); fig.savefig("Mars_Research_Regions_Routes.png", dpi=95); plt.close(fig)

# ---------- sheets 7a / 7b: one region each ----------
for hid, sheet, ext in (("H1", "Sheet 7a", [0, 360, -20, 85]), ("H2", "Sheet 7b", [40, 240, -70, 55])):
    r = REG[hid]; s = r["summary"]; h = r["habitat"]
    fig = plt.figure(figsize=(W_, H_), facecolor="white")
    header(fig, sheet, f"{h['name']} — Research Region Route and Stop Plan")
    ax = fig.add_axes([0.6 / W_, 1.4 / H_, 11.6 / W_, 10.9 / H_])
    basemap(ax); draw_region(ax, hid, big=True)
    ax.annotate(f"{h['name']}\n{h['place']}", (h["lon"] % 360, h["lat"]), xytext=(14, -30), textcoords="offset points",
                fontsize=10.5, weight="bold", color="white", zorder=13, bbox=dict(boxstyle="round,pad=0.35", fc=COL[hid], ec="#111"),
                arrowprops=dict(arrowstyle="-", color="#111"))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    stp = 30 if ext[1] - ext[0] > 250 else 20
    ax.set_xticks(range(ext[0], ext[1] + 1, stp)); ax.set_xticklabels([f"{t}°E" for t in range(ext[0], ext[1] + 1, stp)], fontsize=9)
    ax.set_yticks(range(-60, 91, 15)); ax.set_yticklabels([f"{abs(t)}°{'S' if t < 0 else ('N' if t > 0 else '')}" for t in range(-60, 91, 15)], fontsize=9)
    ax.set_ylim(ext[2], ext[3])
    ax.set_title(f"{s['sites']} sites · {s['road_km']:,} km of road · {s['total_sols']} sols · {s['camps']} camps · {s['depots']} depots",
                 fontsize=14, weight="bold", loc="left", pad=8)
    tp = fig.add_axes([12.6 / W_, 1.4 / H_, 9.1 / W_, 11.1 / H_]); tp.axis("off"); tp.set_xlim(0, 10); tp.set_ylim(0, 26)
    cols = [(0.0, "leg"), (0.7, "from → to"), (5.6, "road km"), (6.9, "drive"), (7.85, "rest"), (8.75, "camps"), (10.0, "arrive")]
    yy = 25.5
    tp.add_patch(Rectangle((0, yy - .45), 10, .9, fc=COL[hid], ec="none"))
    for x, t in cols:
        tp.text(x + (0.05 if x < 1 else 0), yy, t, fontsize=9, weight="bold", color="white", va="center", ha="left" if x < 5 else "right")
    for l in r["legs"]:
        yy -= .78
        if l["leg"] % 2 == 0:
            tp.add_patch(Rectangle((0, yy - .39), 10, .78, fc="#f6f1ea", ec="none"))
        to = "HABITAT (home)" if l["to"] == "HABITAT" else l["to"]
        frm = "HABITAT" if l["frm"] == "HABITAT" else l["frm"]
        tp.text(.08, yy, str(l["leg"]), fontsize=9, va="center", weight="bold", color=DARK[hid])
        tp.text(.7, yy + .17, frm, fontsize=8.4, va="center", color="#555")
        tp.text(.7, yy - .18, "→ " + to, fontsize=8.8, va="center", weight="bold")
        tp.text(5.6, yy, f"{l['road_km']:,}" + "", fontsize=9, va="center", ha="right")
        tp.text(6.9, yy, str(l["drive_sols"]), fontsize=9, va="center", ha="right")
        tp.text(7.85, yy, str(l["rest_sols"]), fontsize=9, va="center", ha="right")
        tp.text(8.75, yy, str(l["camps"]), fontsize=9, va="center", ha="right")
        tp.text(10.0, yy, f"sol {l['arrive_sol']}", fontsize=9, va="center", ha="right", weight="bold")
    yy -= .9
    tp.plot([0, 10], [yy + .35, yy + .35], color="#999", lw=.8)
    tp.text(.08, yy, "TOTAL", fontsize=9, weight="bold", va="center")
    tp.text(5.6, yy, f"{s['road_km']:,}", fontsize=9, weight="bold", va="center", ha="right")
    tp.text(6.9, yy, str(s["drive_sols"]), fontsize=9, weight="bold", va="center", ha="right")
    tp.text(7.85, yy, str(s["rest_sols"]), fontsize=9, weight="bold", va="center", ha="right")
    tp.text(8.75, yy, str(s["camps"]), fontsize=9, weight="bold", va="center", ha="right")
    tp.text(10.0, yy, f"sol {s['total_sols']}", fontsize=9, weight="bold", va="center", ha="right")
    yy -= 1.1
    tp.text(0, yy, "Stops (5 research sols each)", fontsize=10, weight="bold", color=DARK[hid], va="center")
    for st in r["stops"][1:]:
        yy -= .5
        tp.text(.1, yy, f"{st['stop']}. {st['name']}", fontsize=8.8, va="center", weight="bold")
        tp.text(4.6, yy, f"{st['who']} · {st['place']}", fontsize=8.2, va="center", color="#444")
        tp.text(10, yy, f"sol {st['arrive_sol']}–{st['depart_sol']}", fontsize=8.8, va="center", ha="right")
    if s["home_sites"]:
        yy -= .5
        tp.text(.1, yy, f"Home site: {', '.join(s['home_sites'])} — on foot from the habitat", fontsize=8.8, va="center", color="#0b7a3b", weight="bold")
    yy -= .8
    long_leg = max(r["legs"], key=lambda l: l["road_km"])
    tp.add_patch(Rectangle((0, yy - 3.0), 10, 3.15, fc="#fff3cd", ec="#c9a227", lw=1.2))
    tips = [f"Longest leg: {long_leg['frm']} → {long_leg['to']}, {long_leg['road_km']:,} km = {long_leg['drive_sols']} driving sols.",
            f"Depots: {s['depots']} supply drops, placed by robots before the crew lands.",
            f"Route total {s['total_sols']} sols: needs the long-stay mission (~500 sols), leaving {500 - s['total_sols']} sols spare.",
            "All legs routed on MOLA 463 m (road463.py); ground over 12° blocked.",
            f"Steepest 463 m cell on the route: {max(l['max_slope_deg'] for l in LM if l['region'] == hid):.1f}° (limit 12°) — local detail needs HiRISE/CTX checks."]
    for j, t in enumerate(tips):
        tp.text(.2, yy - .3 - j * .55, "• " + t, fontsize=8.5, va="center")
    pdf.savefig(fig); fig.savefig(f"Mars_Region_{hid}_Plan.png", dpi=95); plt.close(fig)
pdf.close()
print("saved")
