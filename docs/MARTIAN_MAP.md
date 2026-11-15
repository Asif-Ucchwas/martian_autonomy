# Martian Map — Project Document (Team MartianAutonomy, NASA Space Apps 2026)

One file for the whole project: plan, routes, terrain checks and data sources.
Updated Sun Nov 15, 2026, 07:30 Central (v5: new Habitat 1 route). Md Asifuzzaman · Team MartianAutonomy · Houston.

Contents
1. Plan and current numbers
2. Route and stop plan (both regions, leg by leg)
3. Terrain results (models, height checks, Gale road, site zoom-ins)
4. Data sources and references (also the NASA data list for submission)

Still kept as separate files: `assumed_values.md` (rover / astronaut / habitat limits with sources), `mission_concept_log.md` (history), `nasa_challenges.md`, and the scripts.

---

## 1. Plan and current numbers
**Superseded:** `mission_concept_log.md` (Fri night) — its 5 colonies + 6 outposts, crew of 6, Gale-first colony and "road = straight × 1.3" are replaced by the decisions below. Keep it only as history and for its fact tables (landings, future missions, speeds).

### Schedule
- **Build until Sunday Nov 15, 12:00 noon Central.** No rushed submission — quality first. Asif decides when to submit (portal closes Sun 23:59 Central).

### Decided
- **2 crew on the surface**, landing together (NASA concept: 4 travel, 2 land, 2 stay in orbit).
- **2 main habitats, 2 missions, 2 research regions.**
  - **Habitat 1 · Ice colony — AP-1**, Arcadia–Amazonis, 39.809N 202.081E. Published ice site (near-surface ice < 1 m, Luzzi et al. 2025, JGR Planets) and one of SpaceX's prime Starship sites (LPSC 2021 poster). Pad at the site centre, habitat 1.02 km away (39.794N 202.074E). Mission 1.
  - **Habitat 2 · Sun colony** — Elysium Planitia, 4.492N 135.605E, 1.2 km from InSight. Mission 2, next window.
- The earlier Habitat 1 spot (39.09N 189.79E, HiRISE ESP_060706_2195) is a **SpaceX candidate landing site** and is stop 2 of Habitat 1's loop.
- Every landing site and planned site belongs to its nearest habitat; each region is explored by one road loop from its habitat.
- Gale is stop 7 of Habitat 2's loop and the validation site — not the colony.
- Delivery: static Leaflet web app (GitHub Pages). Zoomed in, it shows CTX photos (Esri OnMars; copied tiles from that service are detected and hidden) and 24 sharp NASA Trek site mosaics (HiRISE ~25–50 cm, controlled CTX ~6 m), with Viking MDIM in grey filling gaps. A live mission panel follows both crews sol by sol; on phones the side panel is a bottom sheet.

### v5 change (Sun Nov 15, 07:00) — Habitat 1 is no longer a closed loop
- Dropped the 6,258 km Phoenix → Opportunity road (an empty plains crossing made only to close the loop).
- New road **Phoenix → Tianwen-3 zone (Chryse): 3,976 km** on MOLA 463 m, steepest cell 11.4°, 2 km of dust.
- The Pathfinder – Rosalind Franklin – Opportunity branch is driven **out and back**; research on the first visit only.
- Route: Habitat → AP-8 → SpaceX site → Phoenix → Chryse → Pathfinder → Rosalind Franklin → Opportunity → (back) Rosalind Franklin → Pathfinder → Chryse → Viking 1 → AP-9 → Habitat. 13 legs, all re-routed on 463 m (`run_h1_v5.sh`), 0 failed pieces.
- **Habitat 1 now: 18,499 km, 289 sols** (209 driving + 34 rest + 45 research), 196 camps, 23 depots. Dust scenario 307 sols; 9.6 km/h 344 sols. Radiation on the route ~190 mSv.
- Habitat 2 is unchanged (shortest closed loop, Held-Karp). Soft ground on all roads now 3,390 of 41,523 km (8 %).
- The v4 numbers below for Habitat 1 (17,870 km, 275 sols) are kept as history.

### Current numbers — v4: every road on full 463 m MOLA terrain, with dust measured (Habitat 1 superseded by v5 above)
- **Habitat 1 loop (v4, superseded):** 9 sites, 17,870 km, **275 sols**, 189 camps, 22 depots.
- **Habitat 2 loop:** 7 sites + InSight, 18,772 km, **282 sols**, 205 camps, 23 depots.
- Road factors 1.01–1.06. Link road H1–H2: **4,252 km** (4,092 straight), ≈ 46 driving sols — solid line on the map.
- Ground over 12° blocked; steepest 463 m cell on any road 12.0° (Spirit → Mars 3, southern highlands).
- **Soft ground (loose dust, TES thermal inertia < 100): 3,468 of 40,895 km (8.5 %)**, almost all on Viking 1 → AP-9 (1,376 km), Viking 2 → Spirit (1,053 km) and the link road (1,029 km). Both habitats on firm ground (AP-1 156, H2 223).
- **Scenario** — dust driven at half speed (6 km/h): H1 294 sols (+19), H2 296 sols (+14), link ≈ 57 driving sols. Labelled as a scenario: the dust is measured, the slowdown is assumed.
- **Mission calendar (scenario, not a NASA schedule — NASA publishes no crewed-Mars landing date):** Mission 1 / Habitat 1 — cargo + robots launch Feb 2031, crew launch Apr 2033, land Sep 2033, loop Apr 2034 → Jan 2035 (Mars Year 43 spring equinox), leave Feb 2035. Mission 2 / Habitat 2 — cargo Apr 2033, crew launch Jun 2035, land Dec 2035, loop Feb 2036 → Dec 2036 (MY 44 equinox), leave May 2037. Robots get 599 / 623 sols; spare 39 / 152 sols.
- **Robots go first:** 45 depots (one per 800 km), placed by 2 robots per habitat leaving in opposite directions (10 km/h, 8 h/sol): H1 115 sols, H2 126 sols; one robot per habitat 232 / 247 sols; link road 55 sols. Window ≈ 600 sols (DRA 5.0: cargo one opportunity, ~26 months, earlier). **The limit is speed, not time:** the farthest depot is ~9,600 km by road, so a robot must average ~16 km per sol (≥ 2.1 km/h) — Perseverance's best day is 412 m (~39× short) and its self-driving pace ~100 m/h (~21× short). More robots don't help; this needs a new class of fast autonomous rover.
- **Speed check:** our crew rover's 12 km/h equals the Apollo 15 rover's best on level ground; its traverse average was 9.6 km/h. At 9.6 km/h the loops take H1 334 / H2 345 sols — still inside the 372-sol calm season and the 500-sol stay.
- **When to drive:** the calm, low-dust half of the Mars year (northern spring + summer, Ls 0–180) is 194 + 178 = 372 sols. Both loops (275 / 282 sols; 294 / 296 in the dust scenario) fit inside it if started at the northern spring equinox — H1 with 97 sols to spare, H2 with 90. All recorded planet-wide dust storms began in Ls 180–310. For Habitat 1 this also avoids northern winter (−120 °C nights at Viking 2).
- **Radiation** (Curiosity RAD): a full loop is 181 mSv (H1) / 185 mSv (H2) — ~31 % of NASA's 600 mSv career limit. The cruise alone (662 mSv round trip) is over the limit; a whole mission with a 500-sol stay is ~991 mSv, a 30-sol stay ~682 mSv. The roads are not the radiation problem; the flight is.
- A full loop needs a long stay (~500 sols, ~218 spare). **30-sol stay** (one out-and-back trip, home by sol 30, computed by `build_data.py` `stay_plan`): H1 reaches AP-8 and the SpaceX candidate site, home by sol 27 (1,238 km); H2 reaches InSight on foot and Curiosity at Gale by driving its loop backwards, home by sol 22 (1,144 km). 4 of 17 sites. (Earlier docs said H2 reaches the Tianwen-3 Utopia zone at sol 21 — true one-way, but the crew could not get back by sol 30.)

---

## 2. Route and stop plan
Updated Sat Nov 14, 2026, 21:30 Central (v4).
Scripts: `global_roads.py --down 1 --max-slope 5` (pass 1, 5.2 km) → `road463.py` (pass 2, 463 m) → `legs_measured.json` / `legs_463.geojson`;
`ti_roads.py` (dust per leg) → `ti_legs.csv` / `ti_soft.geojson`; `regions_plan.py` (+ `--soft` for the scenario) → `regions_plan.json` / `regions_plan_soft.json`;
map: `regions_map.py` → Mars_Research_Regions_Routes.pdf (Sheets 7, 7a, 7b, real road shapes, dust in purple).

### Model
- Region: every landing site and planned site belongs to its nearest main habitat (great circle).
- Route: one closed loop per region, habitat → all sites → habitat, exact shortest order (Held-Karp).
- Road, pass 1: A* on the MGS MOLA global DEM at 5.2 km cells (16 directions, wrap-around), slopes > 5° blocked so large crater rims are obstacles; |lat| > 80° blocked.
- Road, pass 2 (`road463.py`): every leg re-routed on the full 463 m MOLA DEM in a ±40 km strip around pass 1, cut into ~300 km pieces; Dijkstra on a sparse graph, 16 directions (a knight move needs both crossed cells open); ground over 12° blocked; loose dust costs double time so roads bend around it where the strip allows.
- Travel time on the chosen road: the Gale-road rules (`road_planner.py`) — uphill f = max(0.3, 1 − g/12°), downhill f = max(0.5, 1 − 0.5|g|/12°), side-slope f × max(0.5, 1 − 0.5 s/12°), v = 12 km/h × f.
- Check: on Curiosity → Habitat 2 the new router gives 571.5 km / 51.4 h vs 594.5 km / 52.5 h from `road_planner.py` (8 directions): same time within 2 %, 4 % shorter because 16 directions remove grid zig-zags.
- Driving sols = travel time ÷ 8 h; 1 rest sol after 6 driving sols; 5 research sols per site. One camp at the end of every driving sol; robots pre-place a supply depot every 800 km.
- Dust: TES night thermal inertia (Putzig & Mellon 2007, 20 px/deg) sampled every 2 km on every road; < 100 soft (loose dust), 100–150 caution, ≥ 150 firm.

### Habitat 1 · Ice colony — AP-1, Arcadia–Amazonis (39.809N, 202.081E) — v5 route (current)
**18,499 km · 289 sols** · set route, Opportunity branch out and back

| Leg | From → to | Road km | Max slope | Dust km |
|---|---|---|---|---|
| 1 | Habitat → AP-8 ice site | 68 | 1.0° | 0 |
| 2 | AP-8 ice site → SpaceX candidate site | 551 | 0.9° | 0 |
| 3 | SpaceX candidate site → Phoenix | 2,295 | 4.6° | 5 |
| 4 | **Phoenix → Tianwen-3 zone (Chryse)** (new) | 3,976 | 11.4° | 2 |
| 5 | Chryse → Pathfinder | 717 | 1.4° | 0 |
| 6 | Pathfinder → Rosalind Franklin site | 496 | 3.8° | 0 |
| 7 | Rosalind Franklin site → Opportunity | 1,675 | 5.4° | 0 |
| 8 | Opportunity → Rosalind Franklin site (back) | 1,677 | 5.4° | 0 |
| 9 | Rosalind Franklin site → Pathfinder (back) | 496 | 3.8° | 0 |
| 10 | Pathfinder → Chryse (back) | 717 | 1.9° | 0 |
| 11 | Chryse → Viking 1 | 182 | 1.3° | 0 |
| 12 | Viking 1 → AP-9 ice site | 5,588 | 11.9° | 1,298 |
| 13 | AP-9 ice site → Habitat | 60 | 0.6° | 0 |

Arrivals: AP-8 sol 2, SpaceX site 14, Phoenix 48, Chryse 105, Pathfinder 120, Rosalind Franklin 132, Opportunity 159, Viking 1 205, AP-9 283, home 289.

### Habitat 1 — v4 closed loop (history)
Published ice site (Luzzi et al. 2025) and SpaceX prime site. Checked on CTX terrain (22 m). Ground: thermal inertia 156 (firm).
Loop **17,870 km** · 199 driving + 30 rest + 45 research sols = **275 sols** · 189 camps · 22 depots · dust scenario 294 sols

| Leg | From → to | Road km | Driving sols | Arrive | Max slope | Dust km |
|---|---|---|---|---|---|---|
| 1 | Habitat → AP-8 ice site | 68 | 1 | sol 2 | 1.0° | 0 |
| 2 | AP-8 ice site → SpaceX candidate site | 551 | 6 | sol 14 | 0.9° | 0 |
| 3 | SpaceX candidate site → Phoenix | 2,293 | 25 | sol 48 | 4.6° | 4 |
| 4 | Phoenix → Opportunity | 6,258 | 69 | sol 133 | 5.0° | 6 |
| 5 | Opportunity → Rosalind Franklin site | 1,676 | 19 | sol 160 | 5.4° | 0 |
| 6 | Rosalind Franklin site → Pathfinder | 496 | 6 | sol 171 | 3.8° | 0 |
| 7 | Pathfinder → Tianwen-3 zone (Chryse) | 717 | 8 | sol 185 | 1.9° | 0 |
| 8 | Tianwen-3 zone (Chryse) → Viking 1 | 182 | 2 | sol 192 | 1.3° | 0 |
| 9 | Viking 1 → AP-9 ice site | 5,568 | 62 | sol 269 | 11.9° | 1,376 |
| 10 | AP-9 ice site → Habitat | 60 | 1 | sol 275 | 0.6° | 0 |

Longest leg: Phoenix → Opportunity, 6,258 km, 69 driving sols. Dustiest: Viking 1 → AP-9 (north edge of Tharsis, thermal inertia down to 22).

### Habitat 2 · Sun colony — Elysium Planitia (4.492N, 135.605E, 1.2 km from InSight)
Home site: InSight (on foot). Checked on HiRISE (1 m). Ground: thermal inertia 223 (firm); InSight 236 (published ~200 from orbit).
Loop **18,772 km** · 213 driving + 33 rest + 35 research sols = **282 sols** · 205 camps · 23 depots · dust scenario 296 sols

| Leg | From → to | Road km | Driving sols | Arrive | Max slope | Dust km |
|---|---|---|---|---|---|---|
| 1 | Habitat → Tianwen-3 zone (Utopia) | 1,652 | 18 | sol 21 | 7.7° | 0 |
| 2 | Tianwen-3 zone (Utopia) → Zhurong | 299 | 4 | sol 30 | 1.1° | 0 |
| 3 | Zhurong → Perseverance | 1,880 | 21 | sol 60 | 5.4° | 0 |
| 4 | Perseverance → Viking 2 | 3,291 | 36 | sol 107 | 7.7° | 0 |
| 5 | Viking 2 → Spirit | 4,401 | 49 | sol 169 | 9.1° | 1,053 |
| 6 | Spirit → Mars 3 | 2,363 | 28 | sol 206 | 12.0° | 0 |
| 7 | Mars 3 → Curiosity | 4,314 | 50 | sol 269 | 10.7° | 0 |
| 8 | Curiosity → Habitat | 572 | 7 | sol 282 | 10.6° | 0 |

Longest leg: Viking 2 → Spirit, 4,401 km, 49 driving sols (also the dust belt between Elysium and Amazonis, thermal inertia down to 17). Roughest: Spirit → Mars 3, at the 12° limit in the southern highlands.

### Link road H1 ↔ H2: 4,252 km road (4,092 straight, ×1.04), 365 h ≈ 46 driving sols; 1,029 km of dust (scenario ≈ 57 sols). Solid line in the app and PDF.

### What it means
- The two regions are balanced: 275 and 282 sols (294 / 296 if dust halves the speed).
- A full loop does not fit a 30-sol short stay; it fits a long-stay mission (~500 sols) with ~218 sols spare (~204 in the dust scenario).
- On a 30-sol stay (out and back, home by sol 30): H1 reaches AP-8 and the SpaceX candidate site (home sol 27); H2 reaches InSight on foot and Curiosity at Gale, driving the loop backwards (home sol 22). The Tianwen-3 Utopia zone is 18 driving sols away each way — too far to return in time.
- 45 supply depots in total, pre-placed by robots before the crew lands.

### History
- v4 (Sat 21:10): every leg re-routed on 463 m MOLA (`road463.py`) around v3; dust measured (TES thermal inertia) and avoided where possible — dust on the roads fell from 4,636 km (v3) to 3,468 km. Each leg within ±2 % of v3 except Gale (572 km, no longer a special case).
- v3 (Sat 19:30): 5.2 km cells, 5° limit — H1 17,804 km / 275 sols, H2 18,762 km / 285 sols, link 4,190 km.
- v2 (Sat 17:30): 10.4 km cells, 6° limit — H1 17,690 km / 272 sols, H2 18,570 km / 277 sols, link 4,167 km. The link road crossed a crater (spotted by Asif on CTX imagery) → v3.
- v1 (Sat 15:45): Habitat 1 at 39.09N 189.82E (HiRISE ESP_060706), H1 288 sols / H2 254 sols, link 3,605 km.
- v0 (Sat 15:35): road = straight × 1.3 → H1 343 / H2 292 sols.
- v3 vs v2 road shapes moved up to 107 km (link), 127 km (H1 leg 9), 277 km (H2 leg 7), 314 km (H2 leg 6).

---

## 3. Terrain results
Scripts: `dtm_check.py`, `inside.py`, `road_planner.py`, `site_zoom.py`, `global_roads.py` (in ~/rehearsal on the Legion).
All values below come from real terrain models; limits are from `assumed_values.md`.

### Terrain models used
| Area | Model | Pixel | Source |
|---|---|---|---|
| **H1 · AP-1 (ice colony)** | CTX J20_052424_2201_XN_40N158W__J20_052490_2201_XN_40N158W — file `…_dtm.tif` (7.6 MB) | 22.4 m | NASA MRO / MSSS / USGS |
| H2 InSight (Elysium) | HiRISE DTEEC_037262_1845_036761_1845_U01 (229 MB) | 1.01 m | NASA MRO / UArizona / USGS |
| H2 InSight (backup) | CTX N12_067157_1845_XN_04N224W__F02_036761_1828_XN_02N224W-DEM-geoid-adj (11 MB) | ~20 m | NASA MRO / MSSS / USGS |
| Gale, Bradbury Landing | HiRISE DTEEC_010573_1755_010639_1755_U01 (164 MB); also DTEEC_018854_1755_018920_1755_U01 | 1.01 m | NASA MRO / UArizona / USGS |
| SpaceX candidate site (old H1 spot) | HiRISE DTEEC_060706_2195_060416_2195_A01 (136 MB) + hillshade + RED_C ortho | 1.08 m | NASA MRO / UArizona / USGS |
| Roads (all legs, v3) | MGS MOLA global DEM, read remotely, routed at **5.2 km cells**, slopes > 5° blocked (crater rims = obstacles) | — | NASA MGS / USGS |
| Road Elysium → Gale | MGS MOLA 463 m, cut 134.5–138.5E, 5.5S–5.5N | 463 m | NASA MGS / USGS |
| App / map background | MOLA shaded relief + colour by height, 2048 × 1024 | ~10 km | NASA MGS / USGS |
| App zoomed imagery | CTX global mosaic (~5 m), MDIM greyscale gap filler, HiRISE where available — Esri OnMars tile services | 5–~230 m | NASA / JPL / MSSS / USGS / Esri |

Other terrain near the AP sites (STAC, not downloaded): HiRISE DTEEC_038143_2205_055536_2205_A01 (centre 39.986N 202.602E, ~26 km from AP-1); CTX at AP-8 (F18_042930/F19_043220) and AP-9 (K19_060811/K18_060323).
Catalogue: USGS Astrogeology STAC. Ignore `kaguya_*` collections (Moon data). File names differ by product: some CTX folders use `-DEM-geoid-adj.tif`, others `_dtm.tif` — read the item's `dtm` asset from STAC instead of guessing.

### Validation — terrain vs. published heights
| Point | Local model | MOLA | Published |
|---|---|---|---|
| InSight lander 4.502N 135.623E | HiRISE −2,615.8 m | −2,614 m | ≈ −2,613 m |
| Bradbury Landing 4.589S 137.441E | HiRISE −4,500.9 m | −4,500 m | ≈ −4,500 m |
| AP-1 39.809N 202.081E | CTX −3,939.1 m | −3,920 m | ≈ −4,130 m (news write-up of Luzzi et al.) |
| SpaceX candidate 39.09N 189.80E | HiRISE −3,988.9 m | — | — |

- AP-1: CTX vs MOLA differ by 19 m, consistent with the file's own QA report (median CTX − MOLA difference −24 m, σ 17 m). The published ≈ −4,130 m is ~200 m lower than both NASA maps — it most likely refers to the paper's mapped AP-1 area or a different datum, not this exact point. We show our measured value and cite the published one.

### Roads on 463 m terrain — v4
- Pass 1 (v3): 5.2 km cells, 5° limit — catches craters of ~15 km and up. Pass 2 (v4): 463 m cells, 12° limit, ±40 km strip — catches craters of ~1.5 km and up.
- All 19 legs routed, 0 of 136 pieces failed, 15 s on the Legion. Result: H1 17,870 km / 275 sols, H2 18,772 km / 282 sols, link 4,252 km. Road factors 1.01–1.06.
- Steepest cells: Spirit → Mars 3 12.0°, H1 Viking 1 → AP-9 11.9°, Mars 3 → Curiosity 10.7°, Gale 10.6°; p95 ≤ 3.1° on every leg.
- Limits: boulders and craters under ~1.5 km need HiRISE/CTX checks on the final approach; the ±40 km strip cannot escape dust areas 1,000+ km wide.

### Soft ground — TES thermal inertia
- Data: MGS TES night thermal inertia 2007 (Putzig & Mellon 2007), 20 px/deg, plus its interpolation mask; 87–100 % measured pixels per leg.
- Classes: < 100 loose dust (soft), 100–150 fine-grained (caution), ≥ 150 sand / crust / rock (firm).
- Checks against published landing-site values: InSight 236, Opportunity 186, Curiosity 393, Pathfinder 401.
- On the v4 roads: 32,854 km firm, 4,571 km caution, 3,468 km soft (34 stretches ≥ 20 km). The 463 m router and `ti_roads.py` agree (3,468 vs 3,469 km).
- Sites: all firm except Phoenix (88, soft) and the SpaceX candidate site (133, caution).

### Mission calendar — a scenario
Not a NASA schedule: as of August 2026 NASA publishes no date for a crewed Mars landing. Built from real orbital mechanics (`build_data.py`, `calendar`):
- Launch windows every ~26 months; departure ≈ 85 days before each Mars opposition (oppositions 4 May 2031, 27 Jun 2033, 15 Sep 2035, 19 Nov 2037). Crew transit ~180 days, cargo ~350 days (DRA 5.0); cargo one window ahead of its crew.
- Mars Year 39 began 30 Sep 2026; Mars year = 686.97 days; Ls 180 = 372 sols after Ls 0.

| | Mission 1 · Habitat 1 (ice) | Mission 2 · Habitat 2 (sun) |
|---|---|---|
| Cargo + robots launch / land | Feb 2031 / Jan 2032 | Apr 2033 / Mar 2034 |
| Depots done (2 robots) | May 2032 | Jul 2034 |
| Crew launch / land | Apr 2033 / 30 Sep 2033 | Jun 2035 / 19 Dec 2035 |
| Set-up + local science before the loop | 186 sols | 66 sols |
| Research loop | 9 Apr 2034 → 17 Jan 2035 (MY 43 equinox; dust season starts 26 Apr 2035) | 25 Feb 2036 → 11 Dec 2036 (MY 44 equinox; dust season 13 Mar 2037) |
| Leave Mars (500-sol stay) / home | Feb 2035 / Aug 2035 | May 2037 / Nov 2037 |
| Robot window / spare sols | 599 / 39 | 623 / 152 |
- Departure dates are approximate (± weeks); a real trajectory design would fix them.

### Robots go first — depot placement
Model (`build_data.py`, `depot_plan`): depots every 800 km of loop road; robot A drives along the loop and robot B against it, split to balance their time; each parks at its last depot as a spare rover. Robot pace 10 km/h (as `road_planner.py` robots) on the same slope rules, 8 driving hours per sol, no rest sols.
| Robot | Depots | Road km | Sols |
|---|---|---|---|
| H1-A (along) | 11 | 8,800 | 115 |
| H1-B (against) | 11 | 8,269 | 110 |
| H2-A (along) | 12 | 9,600 | 126 |
| H2-B (against) | 11 | 8,372 | 116 |
| One robot per habitat | 22 / 23 | 17,869 / 18,772 | 232 / 247 |
| Link road (one robot) | 5 | 4,252 | 55 |
- Window: DRA 5.0 sends cargo one opportunity (~26 months) before the crew; cargo transit ~350 days, crew ~180 days → ≈ 620 days ≈ 600 sols on Mars before the crew lands.
- Speed needed to finish in 600 sols: farthest robot ~9,600 km → ~16 km/sol, ≥ 2.1 km/h at 8 h/sol. Perseverance: best sol 412 m, AutoNav ~100 m/h. Not yet demonstrated on Mars.
- Not modelled: depot mass, how many depots one robot can carry, robot power and recharging.

### Rover and crew limits — checked against Curiosity
| What | Value | Basis |
|---|---|---|
| Curiosity's own tilt (telemetry, 690 waypoints, Mount Sharp) | mean 10.0° · p95 18.8° · max 29.1° | Measured |
| Same ground on HiRISE (25 m slope, 608 clean waypoints) | mean 10.2° · soft limit 21.1° (p95) · hard limit 31.6° (p99) | Measured |
| Our roads (MOLA 463 m) | ground over 12° blocked · steepest cell 12.0° · p95 ≤ 3.1° | Modelled |
| Crew rover speed | 12 km/h flat, slower on slopes | Apollo 15 LRV: up to 12 km/h on level ground, 9.6 km/h average |
| Speed sensitivity (9.6 km/h) | H1 334 sols · H2 345 sols (`regions_plan.py --kmh 9.6`) | Modelled |
| Curiosity's pace | median 23.5 m per driving sol · drove on 22 % of sols → 6.5 m/sol | Measured |
| Suited astronaut | 0.61 m/s flat · soft 16.7° · hard 24.2° · 10 km walk-back | Modelled from published data |
- 12° on 463 m cells is deliberately below Curiosity's 21° soft limit: a 463 m cell averages out local relief, so it can hide steeper rover-scale ground. Final approaches are checked on HiRISE / CTX.
- Open issue: HiRISE DTM sits 27.3 m above Curiosity's reported elevation (σ 6.7 m) — unexplained.

### Climate and seasons — measured lander weather
| | Habitat 2 · Sun colony | Habitat 1 · Ice colony |
|---|---|---|
| Source | InSight weather sensors, 1.2 km from the habitat (2018–2022) | Viking Lander 2, Utopia 47.6°N (1976–1980) — nearest measured northern-plains weather; no lander at 40°N Arcadia |
| Temperature | typical sol high −17 °C, low −95 °C | coldest predawn −120 °C (about the CO₂ frost point); thin water frost every winter |
| Pressure | ~700–780 Pa | 730–1,080 Pa through the year |
| Wind / dust | gusts ~17 m/s; thousands of dust-devil pressure signatures, none seen on camera | — |
| Power lesson | InSight's solar panels fell from ~5,000 to ~500 Wh/sol under settled dust; 285 Wh/sol at the end (Dec 2022) | — |

- Season lengths: northern spring 194, summer 178, autumn 142, winter 154 sols; Mars year 668.6 sols.
- Dust season Ls 180–360 (perihelion). The 2018 planet-wide storm began at Ls ~185°; Curiosity measured opacity 8.5; solar-powered Opportunity never recovered.
- Planning result: start each loop at Ls 0 (northern spring equinox); a loop of ≤ 372 sols ends before Ls 180. Late-start margin ≈ 90 sols (≈ 76 in the dust scenario).
- For the Sun colony: a crew can clean panels (InSight could not); keep a non-solar backup for storms.
- Not yet used: Mars Climate Database model values at each habitat's exact spot (next step).

### Radiation dose — Curiosity RAD
Dose = time × measured dose rate; 1 sol = 1.0275 days.
| | Days / sols | Rate | Dose |
|---|---|---|---|
| H1 loop | 275 sols | 0.64 mSv/day (surface, Gale) | 181 mSv |
| H2 loop | 282 sols | 0.64 | 185 mSv |
| Dust scenario loops | 294 / 296 sols | 0.64 | 193 / 195 mSv |
| 500-sol stay | 500 sols | 0.64 | 329 mSv |
| Cruise, each way | 180 days | 1.84 mSv/day (inside MSL) | 331 mSv |
| **Whole mission, 500-sol stay** | | | **~991 mSv** (published template ≈ 1.01 Sv) |
| Whole mission, 30-sol stay | | | ~682 mSv |
| NASA career limit (NASA-STD-3001) | | | 600 mSv; 250 mSv per solar particle event; surface GCR design target < 0.8 mSv/day |
- Not modelled: RAD measured at −4.4 km (Gale); Habitat 1 (−3.9 km) and Habitat 2 (−2.6 km) have slightly less air above them, so dose is likely a little higher there; time inside the habitat / rover shielding would lower it. RAD's first 300 sols were near solar maximum, when cosmic-ray flux is lower.

### Mission 2 road: InSight → Gale (`road_planner.py`, MOLA 463 m, 8 directions, slope limit 12°)
| | Robots 10 km/h | Crew 12 km/h out | Crew back |
|---|---|---|---|
| Road km | 594.1 | 594.1 | 594.5 |
| Straight km | 548.4 | 548.4 | 548.4 |
| Road factor | 1.08 | 1.08 | 1.08 |
| Driving hours | 62.0 | 51.7 | 52.5 |
| Sols (drive + rest) | 8 + 1 = 9 | 7 + 1 = 8 | 7 + 1 = 8 |
| Slope median / p95 / max | 0.2 / 1.85 / 6.8° | same | 0.2 / 1.91 / 6.3° |
| Down / up | 2,806 / 920 m | same | 920 / 2,806 m |

On the 10 km global grid the same leg was 576–578 km. v4 (`road463.py`, 16 directions) gives 571.5 km / 51.4 h, max 10.6°, 2,942 m down / 1,049 m up — the number now used in the plan.

### Site zoom-ins (`site_zoom.py`)
Rules: pad 100 m, ≤ 15° under the pad, tilt ≤ 5° over 200 m; habitat 1–2 km from pad (plume rule);
1 km keep-out around InSight and Curiosity's landing spot; suited walking (0.61 m/s flat, hard limit 24.2°).
Slope baseline: 25 m on HiRISE (12 m cells); ~45 m on CTX (22 m cells) — CTX slopes are slightly smoothed.

| | **H1 · AP-1 (CTX)** | H2 InSight (HiRISE) | Gale Bradbury (HiRISE) | SpaceX candidate (HiRISE) |
|---|---|---|---|---|
| Slope median / p95 | 1.92 / 4.48° | 1.08 / 3.27° | 1.80 / 6.65° | 1.59 / 4.06° |
| Pad-quality ground | **98 %** | 85 % | 86 % | 97 % |
| Over 24.2° (blocked) | 0.01 % | 0.9 % | 0.2 % | 0.1 % |
| Pad | 39.80945N 202.08106E, at site centre, max 1.1°, tilt 0.04° | 4.51879N 135.62539E, 1.01 km from InSight, max 4.4° | 4.57221S 137.44245E, 1.0 km from Bradbury, max 3.1° (cargo / depot pad) | 39.0903N 189.79969E, max 2.3° |
| Habitat / camp | 39.79395N 202.07350E, 1.02 km from pad, max 1.1° | 4.49237N 135.60511E, 1.97 km from pad, max 1.9° | 4.60089S 137.45330E, 1.82 km from pad, max 3.6° (crew camp) | 39.08506N 189.81586E, 1.01 km from pad, max 4.0° |
| Walking zone 1 h / 2 h / 4.5 h | 12.4 / **48.7** / 142.9 km² | 13.3 / 29.2 / 36.2 km² | 7.5 / 18.9 / 33.0 km² | 12.2 / 40.4 / 55.0 km² |

- AP-1 is the flattest site checked and has the largest 2-hour walking zone; the CTX model also covers more ground (143 km² window), so the 4.5 h zone is not cut off by a strip edge as on HiRISE.
- Max slopes of 37–70° in each window are < 1 % of cells (crater walls / model edges); p95 is what matters.
- Gale is the roughest site (smallest 1-h walking zone).
- `site_zoom.py` labels every output "HiRISE" — the AP-1 run used CTX; corrected in the docs and app data.

---

## 4. Data sources and references
Last updated: Sat Nov 14, 2026, 19:30 Central. All public and free.
Tags: **[USED]** in the submitted plan/app · **[USED · prep]** used in prep work (rover validation) · **[LATER]** after submission.
This list doubles as the **NASA data list** required by the Space Apps submission.

### 4.1 NASA terrain data used
| Data | What it gave us | Where | Tag |
|---|---|---|---|
| **MGS MOLA global DEM, 463 m** (Mars_MGS_MOLA_DEM_mosaic_global_463m.tif) | Every road leg: pass 1 at 5.2 km cells, pass 2 at full 463 m (`road463.py`, v4); the app/map background (shaded relief) | https://planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif (2.0 GB, downloaded; earlier read with GDAL `/vsicurl/`) | USED |
| **MGS TES thermal inertia, night 2007 + mask** (global_ti_night_2007.img, global_ti_msk_night_2007.img, 20 px/deg) | Soft-ground (dust) check on every road and site; dust avoidance in the 463 m routing; dust map layer in the app | NASA PDS Geosciences · https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/ | USED |
| **CTX DTM J20_052424_2201__J20_052490_2201** (`_dtm.tif`, 22 m) | Habitat 1 at AP-1: pad, habitat, walking zone; height check vs MOLA | astrogeo-ard S3 · mars/mro/ctx/controlled/usgs/J20_052424_2201_XN_40N158W__J20_052490_2201_XN_40N158W/ | USED |
| **HiRISE DTM DTEEC_037262_1845_036761_1845_U01** (1 m) | Habitat 2 near InSight: pad, habitat, walking zone; InSight height check | astrogeo-ard S3 · mars/mro/hirise/controlled/dtm/ESP_037262_1845_ESP_036761_1845/ | USED |
| **HiRISE DTM DTEEC_010573_1755_010639_1755_U01** (1 m) | Gale: Bradbury height check, cargo/depot pad, crew camp, walking zone | astrogeo-ard S3 · mars/mro/hirise/controlled/dtm/PSP_010573_1755_PSP_010639_1755/ | USED |
| HiRISE DTM DTEEC_018854_1755_018920_1755_U01 (1 m) | Second Gale height check | astrogeo-ard S3 · …/ESP_018854_1755_ESP_018920_1755/ | USED |
| **HiRISE DTM DTEEC_060706_2195_060416_2195_A01** (1 m) | SpaceX candidate site (stop 2 of H1): pad and walking zone | astrogeo-ard S3 · …/ESP_060706_2195_ESP_060416_2195/ | USED |
| CTX DTM N12_067157_1845__F02_036761_1828 (~20 m) | Cross-check near InSight | astrogeo-ard S3 · mars/mro/ctx/controlled/usgs/… | USED |
| USGS Astrogeology STAC API | Finding every terrain model above (collections mro_hirise_socet_dtms, mro_ctx_controlled_usgs_dtms) | https://stac.astrogeology.usgs.gov/api/ | USED |
| **Caltech Murray Lab CTX global mosaic beta01** (~5 m, greyscale) | App zoomed imagery: sharp photos across the zoomed view and the ±50 km road strip (default source) | Esri OnMars tile service https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX/MapServer — credit NASA/JPL/MSSS/Caltech Murray Lab/Esri; found via the Mars Trek layer card and USGS web map b164957a19544f55a8d6a001c952a590 | USED |
| Viking MDIM 2.1 greyscale mosaic (232 m) | App gap filler under CTX/HiRISE when zoomed in | https://astro.arcgis.com/arcgis/rest/services/OnMars/MDIM/MapServer — NASA/USGS/Esri; tile grid checked identical to CTX | USED |
| HiRISE PSP/ESP uncontrolled mosaic (~0.25–1 m, patchy) | App road strip, optional source | https://astro.arcgis.com/arcgis/rest/services/OnMars/HiRISE/MapServer — NASA/JPL/University of Arizona/USGS/Esri | USED |
| MOLA/HRSC blended colour hillshade v2 (~200 m) | App road strip, optional source | https://astro.arcgis.com/arcgis/rest/services/OnMars/MColorDEM/MapServer — NASA/JPL/ESA/DLR/USGS/Esri | USED |
| Viking MDIM 2.1 colour mosaic (232 m) via NASA Trek | App road strip, optional source | https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg | USED |
| InSight APSS / TWINS weather and Viking Lander 2 meteorology | Measured temperature, pressure, wind for the climate card; InSight's solar-power decline | NASA InSight weather service / mission updates; Viking fact sheet (published values) | USED |
| MSL Radiation Assessment Detector (RAD) | Surface dose rate 0.64 ± 0.12 mSv/day and cruise dose rate 1.84 mSv/day → dose per loop and per mission | Hassler et al. 2014; Zeitlin et al. 2013 (published values) | USED |
| HiRISE DTM DTEEC_019698_1750_019988_1750_U01 + ortho (Mount Sharp) | Rover-limit validation against Curiosity tilt (prep) | astrogeo-ard S3 | USED · prep |
| NASA Trek layers (Viking colour, MOLA shade, curiosity_hirise_mosaic) | Prep basemaps | trek.nasa.gov | USED · prep |

### 4.2 Site positions used
| Site | Position | Source |
|---|---|---|
| 11 landing sites (Mars 3, Viking 1 & 2, Pathfinder, Spirit, Opportunity, Phoenix, Curiosity, InSight, Perseverance, Zhurong) | Published landing coordinates (see `mission_concept_log.md` §2) | NASA/JPL and mission publications |
| **AP-1** | 39.809N 202.081E (HiRISE image centre ESP_052490_2200, acquired 7 Oct 2017, "Candidate Red Dragon Landing Site in Arcadia Planitia") | https://hirise.lpl.arizona.edu/ESP_052490_2200 |
| **AP-8** | 40.735N 201.272E (ESP_043220_2210, 16 Oct 2015) | https://hirise.lpl.arizona.edu/ESP_043220_2210 |
| **AP-9** | 40.016N 203.330E (ESP_060323_2205, 9 Jun 2019, "Candidate Landing Site for SpaceX Starship in Arcadia Region") | https://hirise.lpl.arizona.edu/ESP_060323_2205 |
| SpaceX candidate site | 39.090N 189.790E (ESP_060706_2195, 9 Jul 2019, "Candidate Landing Site for SpaceX Starship Near Arcadia Planitia", stereo pair with ESP_060416_2195) | https://hirise.lpl.arizona.edu/ESP_060706_2195 |
| Rosalind Franklin (ESA) | Oxia Planum 18.20N 335.45E | ESA |
| Tianwen-3 zones | Representative points in Chryse (23.5N 315E) and Utopia (23.5N 115E) — approximate; 8 areas shortlisted, final site due end of 2026 | China Daily / The Star (Sep 2026), Space.com |

AP image IDs come from the LPSC 2021 poster "SpaceX Starship Landing Sites on Mars" (AP1 = ESP_052490_2200, AP9 = ESP_060323_2205 prime; AP8 = ESP_043220_2210 backup), as reported by Behind the Black (Mar 2021). AP-8's image matches the Luzzi et al. figure caption ("terraced crater 1.4 km W of AP-8, HiRISE ESP_043220_2210") and AP-1's matches their polygon-terrain image ESP_052490_2200. Image centres are used as site positions; the exact mapped areas may differ by a few km.

### 4.3 Literature and news used
- **Luzzi, E., Heldmann, J.L., Williams, K.E., Nodjoumi, G., Deutsch, A., Sehlke, A. (2025).** Geomorphological evidence of near-surface ice at candidate landing sites in northern Amazonis Planitia, Mars. *JGR Planets* 130(5). doi:10.1029/2024JE008724 — AP-1, AP-8, AP-9; ice < 1 m deep. (USGS pubs record: https://pubs.usgs.gov/publication/70266466; open access)
- University of Mississippi press release (Jun 2025) and ScienceDaily (Dec 27, 2025) — ice less than 1 m below the surface in Amazonis Planitia.
- News write-up "Frozen Treasure: Mars Ice Deposits Found Inches Below Surface" (D. Freeman, May 19, 2025; seen via a forum repost) — AP-1 elevation ≈ −4,130 m with 31 m relief. Secondary source; ~200 m lower than MOLA and CTX at the image centre — not used for numbers, cited only for comparison.
- LPSC 2021 poster "SpaceX Starship Landing Sites on Mars" — prime sites AP1, AP9 (https://www.hou.usra.edu/meetings/lpsc2021/pdf/2420.pdf).
- Tianwen-3: eight landing areas shortlisted, final site by end of 2026 (China Daily / The Star, Sep 2026; Space.com).
- Mars calendar: Clancy et al. (2000), JGR 105, 9553 (Mars Year count); Piqueux et al. (2015), Icarus 251, 332–338 (year tables); MY 39 start 30 Sep 2026 (EarthSky). Mars oppositions 2029–2037 (Universe Today / Phys.org list).
- Drake, B.G. (ed.) (2009). Human Exploration of Mars Design Reference Architecture 5.0, NASA/SP-2009-566 — forward-deployed cargo one opportunity before the crew; ~350-day cargo transit, ~180-day crew transit, ~500-day surface stay.
- Perseverance driving records (NASA/JPL): best single sol 412 m; AutoNav ~100 m/h.
- Apollo 15 Lunar Roving Vehicle traverse record (NASA experiment operations summary): 27.9 km odometer, average 9.6 km/h, up to 12 km/h on level ground.
- **Banfield, D., Spiga, A., et al. (2020).** The atmosphere of Mars as observed by InSight. *Nature Geoscience* 13, 190–198, doi:10.1038/s41561-020-0534-0.
- NASA Mars facts: season lengths (northern spring 194, summer 178, autumn 142, winter 154 sols); NASA/JPL InSight power updates (2022); Guzewich et al. (2019), GRL 46 — 2018 storm, opacity 8.5 at Gale.
- **Hassler, D.M. et al. (2014).** Mars' surface radiation environment measured with the Mars Science Laboratory's Curiosity rover. *Science* 343(6169), doi:10.1126/science.1244797 — 0.64 ± 0.12 mSv/day on the surface.
- **Zeitlin, C. et al. (2013).** Measurements of energetic particle radiation in transit to Mars on the Mars Science Laboratory. *Science* 340 — 1.84 mSv/day in cruise; ~662 mSv for two 180-day transits.
- NASA-STD-3001 Vol. 1 (OCHMO technical brief OCHMO-TB-020): career limit 600 mSv; 250 mSv per solar particle event.
- **Putzig, N.E., Mellon, M.T. (2007).** Apparent thermal inertia and the surface heterogeneity of Mars. *Icarus* 191, 68–94 — the TES thermal-inertia maps used for soft ground (NASA PDS mgst_9001).
- Golombek, M. et al. (2017). Selection of the InSight landing site. *Space Science Reviews* 211 — orbital thermal inertia ~200 at the InSight site, used as a check (our value 236).
- Rover / astronaut / habitat limits: see `assumed_values.md` (Minetti 2002, Kram 1997, Norcross 2010, Vos 2007, JPL MSL engineering constraints, Hoffman & Bussey 2016, Hassler 2014).
- NASA crewed-Mars architecture (2 on the surface, 2 in orbit): NASA SAC21 architecture studies.

Esri OnMars tile grid (checked): GCS Mars 2000 sphere (wkid 104971, R 3,396,190 m), origin −180°/90°, 512 px tiles, level n = 180/2^n degrees per tile — same grid as Leaflet EPSG4326 with tileSize 512, zoomOffset −1. CTX and HiRISE mosaics are uncontrolled (may sit a few hundred metres off). Other services in that web map: THEMIS day/night IR (OnMars/THEMIS_DayIR, THEMIS_NightIR), HiRISE stereo orthos (OnMars/HiRISELS), MDIM (OnMars/MDIM).

### 4.4 Still to add
Done tonight and moved to 4.1: MOLA 463 m per leg, thermal inertia (TES instead of THEMIS), RAD radiation (published rates; shielding model still later), climate card (measured lander weather; MCD model values still to add).
| Data | What it would add | Where | Tag |
|---|---|---|---|
| SWIM ice maps | Ice consistency map under Habitat 1 | SWIM project data release — site down (HTTP 523) on Sat Nov 14 evening; retry | NEXT |
| Mars Climate Database | Temperature and dust by season per habitat | LMD web interface | LATER |
| Perseverance waypoints (M20) | Jezero detail | mars.nasa.gov MMGIS | LATER |

---

Made with AI assistance (Claude).
