# Martian Map — The Math & Physics Behind It

Nov 13, 2026 · @Md Asifuzzaman

## How to use this doc

Every formula here is one we actually used in Martian Map, shown with a worked example from our own data, so you can check each number yourself.

Each section follows the same order: the idea in plain words, the formula, a worked example with real numbers, then where it lives in the code. Read it in order the first time; afterwards use the formula sheet at the end as a lookup.

| Section | Where it shows up in the project |
| --- | --- |
| Mars geometry | Converting DTM bounds, every lat/lon ↔ metres step |
| Distances on a sphere | Click-to-click distance, circle sizes on the map |
| Map tiles and zoom | `make_tiles.py`, Leaflet zoom limits |
| Terrain from elevation | Slope, roughness, hillshade (Stage 2) |
| Statistics | `validate_slope_valid.py`, the rover limits |
| Path planning | `planning/fmm.py`, `planning/dijkstra.py` (Stage 4) |
| Collision checking | `planning/collision.py` (Stage 6) |
| Walking physics | `astronaut_walk.py`, the walking zone (Stage 5) |
| Rover motion | `rover_speed.py`, rover travel time |
| Radiation | Dose along the astronaut's route (Stage 6) |

## 1. Mars geometry and coordinates

Our data treats Mars as a perfect sphere of radius R = 3,396,190 m, and stores positions in metres on a flat grid, so converting between degrees and metres is one multiplication.

The DTM uses the projection **IAU 49910**: equirectangular ("plate carrée"), standard parallel 0°, central meridian 0°. On this grid, x is proportional to longitude and y to latitude:

```math
x = R\,\lambda, \qquad y = R\,\varphi \qquad (\lambda, \varphi \text{ in radians})
```

Going back, λ = x / R and φ = y / R. One degree of arc on Mars is therefore:

```math
\frac{\pi R}{180} = \frac{\pi \times 3\,396\,190}{180} \approx 59\,274 \text{ m per degree}
```

**Worked example.** Our DTM's bounds came back in metres; dividing by R gave latitude −5.0409° to −4.7291° and longitude 137.3122° to 137.4390°. Check the size both ways:

| Check | From degrees | From pixels | Match |
| --- | --- | --- | --- |
| Height | 0.3118° × 59,274 = 18,482 m | 18,270 px × 1.0117 m = 18,484 m | yes |
| Width | 0.1268° × 59,274 = 7,516 m | 7,426 px × 1.0117 m = 7,513 m | yes |

**Why the early `window: (0,0)` bug happened.** We once passed a box in degrees to a file whose coordinates are metres. A box of “137.3 to 137.4” metres sits near the map origin, nowhere near Gale, so the read returned nothing. The fix was the `xy()` function: multiply radians by R.

**The one distortion to know.** Equirectangular stretches east–west distances away from the equator. A true east–west distance is R × cos φ × Δλ. At Gale (φ ≈ −4.9°), cos φ = 0.9963, so the grid overstates east–west lengths by only 0.37%. That is small enough to ignore here, but not near the poles.

**Planetocentric latitude.** “Ocentric” in the CRS name means latitude is measured from Mars's centre, not perpendicular to an ellipsoid. On a sphere the two are the same, which is one reason the sphere is convenient.

## 2. Distances on a sphere

The straight-line distance between two clicks on Mars is a great-circle distance, computed with the haversine formula and Mars's radius, not Earth's.

```math
a = \sin^2\!\left(\frac{\Delta\varphi}{2}\right) + \cos\varphi_1 \cos\varphi_2 \sin^2\!\left(\frac{\Delta\lambda}{2}\right), \qquad d = 2R \arcsin\sqrt{a}
```

The haversine form stays accurate for very short distances, where the simpler law-of-cosines formula loses precision to rounding.

**Worked example (Task 7 rehearsal).** Clicks at (−4.82849°, 138.5321°) and (−4.75708°, 135.98328°). Haversine with R = 3,396,190 m gives **150,612 m**, exactly what the app printed. Sanity check by hand: 2.549° of longitude × 59,274 m × cos 4.8° ≈ 150.6 km. With Earth's radius the same clicks would read about 283 km, which is how you catch the mistake.

**The Leaflet circle trap.** Leaflet draws a circle of radius r metres assuming Earth's radius, 6,371,000 m. To draw a circle that is r metres on Mars, pass a larger number:

```math
r_{\text{Leaflet}} = r_{\text{Mars}} \times \frac{6\,371\,000}{3\,396\,190} \approx 1.876\, r_{\text{Mars}}
```

Without this factor, every walking zone and buffer on the map would be drawn 1.876 times too small. The rehearsal app applies it; the real app must too.

## 3. Map tiles and zoom

A tiled map is a pyramid: each zoom level doubles the detail and quadruples the tile count, and the right maximum zoom is where one screen pixel equals one data pixel.

In the lat/lon tile scheme Trek and our map use (Leaflet's EPSG4326), zoom 0 is 2 × 1 tiles of 256 px covering the whole planet. At zoom z, each tile spans D degrees:

```math
D = \frac{180^\circ}{2^{z}}, \qquad \text{columns} = 2^{z+1}, \qquad \text{rows} = 2^{z}
```

The tile holding a point (φ, λ) is found by counting tiles from the top-left corner (−180°, +90°):

```math
x = \left\lfloor \frac{\lambda + 180}{D} \right\rfloor, \qquad y = \left\lfloor \frac{90 - \varphi}{D} \right\rfloor
```

The **native zoom** is where the data's pixel size Δ (in degrees) matches a screen pixel, D/256:

```math
z^{*} = \log_2 \frac{180}{256\,\Delta}, \qquad \Delta = \frac{\text{resolution in metres}}{59\,274}
```

**Worked examples.**

| Data | Resolution | Native zoom z\* | We tiled to |
| --- | --- | --- | --- |
| DTM hillshade | 1.0117 m | 15.33 | 15 |
| HiRISE ortho | 0.253 m | 17.33 | 16 |

The ortho's native zoom is exactly 2 above the hillshade's because 0.253 m is a quarter of 1.0117 m, and log₂ 4 = 2. Ground size per screen pixel is 59,274 × D / 256: about 10.2 m at zoom 12, 1.27 m at zoom 15 and 0.64 m at zoom 16. The test tile for Curiosity's first waypoint at zoom 16 was x = 115553, y = 34489; Trek's server uses the same numbers in {z}/{y}/{x} order.

**Why tile counts explode.** Each zoom level has 4× the tiles of the one before. Our ortho went from 1,042 tiles at zoom 15 to 4,010 at zoom 16, and zoom 17 would add roughly 15,000 more.

**Resampling.** When a tile shows less detail than the data (z below native), we use **average** resampling: each screen pixel is the mean of the data pixels under it, which prevents shimmering patterns (aliasing). When zooming past the data, **bilinear** resampling blends the four nearest pixels for a smooth result.

**Contrast stretch.** Raw pixel values were mapped to 0–255 using the 1st and 99th percentiles of the whole image:

```math
v' = 255 \times \frac{v - p_{1}}{p_{99} - p_{1}}, \quad \text{clipped to } [0, 255]
```

Because our strip contains very dark dunes, its percentiles differ from those of NASA's blended mosaic. That is why the ortho looked darker than the Trek layer beside it.

## 4. Terrain from elevation

Slope is the steepness of the elevation surface, and the distance you measure it over (the baseline) matters as much as the formula: short baselines turn elevation noise into fake steep slopes.

**The DTM.** A digital terrain model is a grid of elevations z(i, j) with cell size Δ (1.0117 m for ours). HiRISE DTMs are built from two images taken from slightly different angles (stereo), like human depth perception. Their stated accuracy is about ±1.3 m vertically and ±100 m horizontally, because they are tied to the coarser MOLA laser altimeter.

**Slope by Horn's method.** Take the 3 × 3 neighbourhood of a cell, labelled a b c / d e f / g h i from top-left. Horn's method estimates the two gradients with weighted differences, then combines them:

```math
\frac{\partial z}{\partial x} = \frac{(c + 2f + i) - (a + 2d + g)}{8\Delta}, \qquad \frac{\partial z}{\partial y} = \frac{(g + 2h + i) - (a + 2b + c)}{8\Delta}
```

```math
\text{slope} = \arctan\sqrt{\left(\frac{\partial z}{\partial x}\right)^{2} + \left(\frac{\partial z}{\partial y}\right)^{2}}
```

The middle row and column get weight 2 because they sit closest to the centre cell; this makes the estimate less sensitive to single noisy pixels.

**Baseline and error.** If each elevation has an error of about σ, a slope measured over a baseline L can be wrong by roughly:

```math
\delta\theta \approx \arctan\frac{\sigma}{L}
```

With σ = 3 m: over L = 20 m the error is about 8.5°; over L = 200 m it is under 1°. To use a 25 m baseline, we compute slope on a grid resampled to 25 m cells (or with neighbours 25 m apart) rather than 1 m.

**What we measured.** At Curiosity's 608 clean waypoints, the slope's 95th percentile drops as the baseline grows: 27.2° at 1 m, 21.1° at 25 m, 18.4° at 51 m. Short baselines read too steep because they include noise; very long ones smooth away real slopes. Section 5 explains how we chose 25 m.

**Roughness.** We define roughness as the standard deviation of elevation within a small window around each cell:

```math
\text{roughness} = \sqrt{\frac{1}{N}\sum_{k=1}^{N} (z_k - \bar{z})^{2}}
```

It is high on boulder fields and broken ground even where the average slope is gentle, which is why the cost surface uses both.

**Hillshade.** A hillshade is a picture computed from elevation: each cell's brightness is how directly it faces a pretend sun. With sun zenith Z (90° minus altitude) and azimuth A, a cell with slope S and aspect (facing direction) α gets:

```math
h = 255 \left[\cos Z \cos S + \sin Z \sin S \cos(A - \alpha)\right]
```

That is why the hillshade looked like a white plastic model next to the photo: it shows shape only, not surface colour.

**Edge artifacts.** Near the edges of a stereo strip, only one image sees the ground well, so elevations are interpolated across flat triangles. That is the jagged sawtooth visible in the hillshade, and why we dropped waypoints within about 37 m of the edge.

## 5. Statistics we used

Correlation could not pick a slope baseline, so we chose it by matching distributions, and then converted the rover's limits into DTM units by matching percentiles.

**Pearson correlation** measures how well two quantities rise and fall together, from −1 to +1:

```math
r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^{2}}\,\sqrt{\sum (y_i - \bar{y})^{2}}}
```

**How precise is r?** Its standard error is roughly:

```math
SE(r) \approx \frac{1 - r^{2}}{\sqrt{n - 1}}
```

With n = 608 and r ≈ 0.14, SE ≈ 0.04. Our five baselines gave r between 0.127 and 0.150, a spread of 0.023: smaller than the uncertainty, so they cannot be told apart. The correlation is still real, though. The test statistic t = r√(n−2) / √(1−r²) = 3.45 for r = 0.139, which corresponds to p ≈ 0.0006.

**Why r is low anyway: range restriction.** Rover drivers avoid steep ground, so the waypoints only sample gentle slopes. Squeezing the range of x always lowers r, even when the underlying relationship is strong. Other reasons: the DTM's true resolution is 10–20 m, the rover's wheelbase is 2.7 m, and a wheel on a rock tilts the rover regardless of the slope.

| Baseline | DTM slope mean | DTM slope p95 | r with rover tilt |
| --- | --- | --- | --- |
| 1 m | 12.0° | 27.2° | +0.141 |
| 5 m | 11.2° | 25.6° | +0.150 |
| 11 m | 10.6° | 23.6° | +0.149 |
| 25 m | 10.2° | 21.1° | +0.139 |
| 51 m | 9.6° | 18.4° | +0.127 |

Rover tilt at the same 608 points: mean 10.2°, p95 18.5°. The 25 m mean matches exactly; its p95 reads 2.6° steeper, which errs on the safe side.

**Percentiles.** The p-th percentile is the value below which p% of the data falls. p95 ignores the top 5%, so one bad point cannot move it, unlike the maximum.

**Quantile matching.** The planner reads DTM slope, but the rover's limits were measured as tilt. To convert a limit between the two, take the same percentile in each distribution:

```math
F_{\text{DTM}}(s) = F_{\text{tilt}}(t) \;\Rightarrow\; s = F^{-1}_{\text{DTM}}\big(F_{\text{tilt}}(t)\big)
```

In words: the rover's 95th-percentile tilt corresponds to the DTM's 95th-percentile slope, 21.1°. That becomes the soft limit. The hard limit uses p99 = 31.6° rather than the maximum of 43.1°. Curiosity's tilt never exceeded 29.1°, so a 43° reading means a waypoint landed on the wrong pixel (the DTM's ±100 m horizontal accuracy), not that the rover drove up 43°.

**The contamination lesson.** The first validation filled missing pixels with the mean elevation before computing slope. The 71 waypoints sitting on missing data then got slopes from a fake flat surface or a fake cliff at its edge. That produced r = 0.184, a “25 m wins” result and a +41 m elevation offset, all of which shrank on clean data (r = 0.139, offset +27.3 m, σ 6.7 m). Rule: after filling gaps for a calculation, always exclude the filled points from the statistics.

## 6. Path planning math

The planner turns terrain into a travel-time field with the Fast Marching Method, then walks downhill through that field from the goal to the start to get the route.

**Cost surface.** Each layer (slope, roughness) is scaled to 0–1 and combined with user weights wₖ. Slope above the hard limit is set to infinity, not just a big number, so impassable stays different from merely expensive:

```math
C(\mathbf{x}) = \begin{cases} \sum_k w_k\, \hat{L}_k(\mathbf{x}) + c_0 & \text{slope} \le s_{\text{hard}} \\ \infty & \text{slope} > s_{\text{hard}} \end{cases}
```

The small constant c₀ > 0 makes flat, smooth ground cost something, so the planner still prefers shorter routes. Speed is the inverse of cost: F = 1/C.

**The Eikonal equation.** T(x) is the earliest time a wave starting at the source reaches point x, moving at local speed F(x). It satisfies:

```math
\lvert \nabla T(\mathbf{x}) \rvert = \frac{1}{F(\mathbf{x})}, \qquad T(\text{source}) = 0
```

Pictured: drop a stone in a pond where the water is thicker in some places; T is when the ripple arrives at each spot.

**Fast Marching Method (FMM).** FMM computes T outward from the source, always finalising the cell with the smallest tentative time, like Dijkstra. The difference is the update. Instead of adding one edge length, it solves a small quadratic using the best neighbour in x (Tₓ) and in y (Tᵧ):

```math
\max(T - T_x, 0)^{2} + \max(T - T_y, 0)^{2} = \left(\frac{\Delta}{F}\right)^{2}
```

This lets the wavefront travel at any angle, not just along grid directions, which is why FMM suits continuous weighted terrain.

**Getting the route (backtrace).** Start at the goal and repeatedly step against the gradient of T, which always points back towards the source along the fastest path:

```math
\mathbf{x}_{k+1} = \mathbf{x}_k - h\, \frac{\nabla T(\mathbf{x}_k)}{\lvert \nabla T(\mathbf{x}_k) \rvert}
```

**Why not plain Dijkstra?** On an 8-connected grid, Dijkstra can only move at multiples of 45°. A straight line at 22.5° is approximated by a staircase that is up to 8.2% longer than the true distance. FMM's error is far smaller: in our Stage 0 test, a diagonal of true length 70.71 came out as 70.44, a 0.4% error. Dijkstra stays as the fallback because it is simple and hard to break.

**Isochrones and the walking zone.** Run FMM from the habitat, and every cell gets its walking time T. All cells with T ≤ τ form the zone reachable in time τ, and its boundary is an isochrone. For out-and-back trips we shade cells where 2T ≤ the suit-time budget.

**Caution: uphill is not downhill.** Our astronaut walks faster downhill than uphill, but standard FMM assumes speed is the same in every direction at a point (isotropic). Using the uphill speed for every direction keeps the zone conservative. Direction-dependent (anisotropic) planning is a known extension for later.

## 7. Collision checking geometry

A route is a chain of straight segments, and the rule used to check each segment decides whether it can clip through blocked cells; your earlier report found that 73–100% of paths under a sampled rule entered an obstacle cell, against none under the exact rule.

**Sampled rule.** Check points along the segment every s metres. A segment of length ℓ is tested at about ℓ/s points. Anything narrower than s, or a corner the segment only grazes, can fall between two samples and be missed.

**Exact rule.** Find every grid cell the segment passes through, and reject the segment if any of them is blocked. Grid-traversal algorithms (for example Amanatides–Woo) step from cell to cell along the line. A safety margin m is applied by inflating blocked cells by m first, equivalent to keeping the segment at least m away from them.

**Grazing rate.** After planning, resample the final route at a spacing much smaller than a cell and count how many points land in impassable cells:

```math
\text{grazing rate} = \frac{\#\{\text{resampled points in impassable cells}\}}{\#\{\text{resampled points}\}}
```

A sampled-rule route should show grazing; an exact-rule route should show none. Reporting both side by side on Mars terrain is the project's headline comparison.

## 8. Physics of walking on Mars in a suit

In a 121 kg suit, an astronaut on Mars weighs 95% of their Earth body weight, so they climb almost as hard as on Earth while walking at a slower natural pace: 0.61 m/s on flat ground, slowing to 0.14 m/s on a 10° climb at the same effort.

**Walking as an inverted pendulum.** In each step the body vaults over a stiff leg, like an upside-down pendulum. Gravity has to pull the body back down around that arc; if you go too fast, it cannot, and you must run. The **Froude number** compares the two effects:

```math
\mathrm{Fr} = \frac{v^{2}}{g\,L}
```

where v is speed, g gravity and L leg length (about 0.9 m). Humans switch from walking to running at Fr ≈ 0.5, on Earth and in reduced gravity alike (Kram et al., 1997).

**What that means on Mars (g = 3.71 m/s²).** The fastest walk is √(0.5 × 3.71 × 0.9) = 1.29 m/s. Any comfortable speed scales the same way, with the square root of gravity:

```math
v_{\text{Mars}} = v_{\text{Earth}} \sqrt{\frac{g_{\text{Mars}}}{g_{\text{Earth}}}} = 1.0 \times \sqrt{0.378} = 0.61 \text{ m/s}
```

NASA's suited treadmill tests used 0.56–0.97 m/s, consistent with this.

**Cost of transport.** Physiologists measure walking effort as metabolic energy per kilogram per metre, C in J/(kg·m). Minetti et al. (2002) measured C on slopes from −45% to +45% grade: 1.64 on the flat, 4.68 at +10%, 8.07 at +20% and 17.33 at +45%.

**Why uphill is so expensive: lifting work.** Climbing means lifting your weight. Per metre walked on gradient i, the lifting work is g sin(arctan i) per kilogram, and muscles convert metabolic energy to mechanical work at an efficiency η of about 25%:

```math
C(i) \approx C(0) + \frac{g \sin(\arctan i)}{\eta}
```

Check at +45% on Earth: 9.81 × 0.410 / 0.25 + 1.64 = 17.7 J/(kg·m), against 17.33 measured. Uphill cost is almost entirely lifting, so it scales with the weight being lifted.

**Adding the suit.** NASA found that suit weight, not pressure, causes most of the difference in effort between suits. The weight carried on Mars is:

```math
W = (m_{\text{body}} + m_{\text{suit}})\, g_{\text{Mars}} = (80 + 121) \times 3.71 = 746 \text{ N}
```

An 80 kg person on Earth weighs 785 N, so the ratio is 0.95. On Mars the suit cancels most of the low-gravity advantage. That is why our model scales Earth's measured costs by 0.95.

**From cost to speed: constant effort.** We assume the astronaut keeps the same metabolic power P as on the flat and slows down uphill. Power is cost times speed (per kg), so:

```math
P = C(0)\, v_{\text{flat}} \quad\Rightarrow\quad v(\theta) = v_{\text{flat}} \frac{C(0)}{C(\theta)}
```

At 10° (gradient 0.176) the cost is about 4.4 times the flat cost, so v = 0.61 / 4.4 = 0.14 m/s. Holding flat-ground speed there would need 4.4 times the effort instead.

&#91;embedded content: computed with astronaut\_walk.py (Minetti 2002 costs, Mars gravity, 121 kg suit) · slopes 0–24°\]

The downhill curve rises first because gentle descents cost less than flat walking, then falls as braking on steep slopes takes effort.

**Slope limits.** Gradient and angle are related by i = tan θ. The soft limit 16.7° = arctan 0.30 is the steepest grade NASA tested in a suit; the hard limit 24.2° = arctan 0.45 is the steepest grade with any human walking data.

**Walk-back time.** Time is distance over speed: 10 km at 0.61 m/s is 16,260 s, or 4.5 hours. All at 10° uphill, it becomes about 20 hours, which is why the habitat's walking zone is shaped so strongly by terrain.

## 9. Rover motion

Curiosity's tilt combines its roll and pitch, and its travel rate is set by mission operations, not by the slope: 23.5 m on a typical driving sol, 6.5 m per sol overall.

**Roll, pitch and tilt.** Roll is rotation about the rover's forward axis (side-to-side lean); pitch is rotation about its side axis (nose up or down). Tilt is the angle between the rover's up-axis and true vertical, which combines both:

```math
\cos(\text{tilt}) = \cos(\text{roll})\,\cos(\text{pitch})
```

**Worked example from our file.** The first waypoint has roll 2.79° and pitch 5.13°. Then cos(tilt) = 0.99881 × 0.99599 = 0.99482, so tilt = 5.84°, exactly the `tilt` value stored in the file. You can verify any waypoint this way.

**Tilt is not slope.** Tilt is what the rover's body felt over its 2.7 m wheelbase, including rocks under single wheels. DTM slope is the ground's average steepness over the chosen baseline. That difference is why Section 5 needed quantile matching to convert between them.

**Pace statistics** (sols 1930 to 5070, from `rover_speed.py`):

| Measure | Value |
| --- | --- |
| Distance per driving sol | median 23.5 m, p95 58.4 m, max 106.1 m |
| Share of sols with driving | 22% |
| Mission pace (all sols) | 6.5 m per sol |

A sol (Mars day) lasts 24 h 39 min 35 s. Travel time in sols is distance divided by pace: 1 km takes about 1000 / 23.5 ≈ 43 driving sols, or 1000 / 6.5 ≈ 154 sols at mission pace, about five Earth months.

**Why pace ignores slope.** How far Curiosity drives each sol depends on daily planning, communication windows with Earth, power and science stops. Slope changes which route is chosen, not how fast the rover goes along it, so the planner converts route length to sols with a constant rate.

## 10. Radiation

An astronaut's dose on a walk is the surface dose rate measured at Gale (0.67 mSv per day) times the time spent, reduced by the share of sky that terrain blocks.

**Dose and dose equivalent.** Absorbed dose D is energy deposited per kilogram of tissue, measured in gray (1 Gy = 1 J/kg). Different particles do different biological damage for the same energy, so each is multiplied by a weighting factor wᵣ. The result, dose equivalent H, is measured in sieverts (Sv):

```math
H = \sum_{R} w_R\, D_R
```

**The measured baseline.** Curiosity's RAD instrument recorded an average galactic-cosmic-ray dose equivalent of 0.67 mSv per day at the surface, August 2012 to June 2013, during a solar maximum (Hassler et al., 2014). It is a single location and period, which is why the app labels it as a baseline, not a dose map.

**Terrain shielding: sky-view factor.** Cosmic rays arrive from all over the sky, so a canyon or cliff that hides part of the sky blocks part of the dose. At each route point we find the horizon elevation angle hₖ in N = 8 directions. The fraction of the upper hemisphere still open is:

```math
\text{SVF} = 1 - \frac{1}{N} \sum_{k=1}^{N} \sin h_k
```

This follows from geometry: the sky above an elevation h covers a share 1 − sin h of the hemisphere's solid angle. The shielded rate is then Ḣ ≈ 0.67 mSv/day × SVF. It is a simplification: it ignores secondary particles produced in the ground and treats the sky as uniformly bright in cosmic rays.

**Cumulative dose along a route.** Add up rate times time at each step:

```math
H_{\text{route}} = \sum_{i} \dot{H}_i\, \Delta t_i
```

Example: a 4.5-hour walk under open sky gives 0.67 × 4.5 / 24 ≈ 0.13 mSv. A single walk is small; what matters over a mission is the total surface time, which is why the app reports dose rather than hiding it.

## 11. The road planner (Space Apps build, Nov 14–15)

Sections 1–10 are the foundations from the Gale pilot. This section is the math behind the submitted app: how every road between the two habitats and the 17 sites was found, timed and turned into a sol-by-sol plan. Code: `global_roads.py` (pass 1), `road463.py` (pass 2), `ti_roads.py` (dust), `regions_plan.py` and `build_data.py` (plan, depots, seasons, dose).

**11.1 Pass 1 — A\* on the whole planet.** The MOLA global DEM is resampled to 4096 × 2048 cells. On a sphere of radius R = 3,389.5 km each row is one cell high, and a cell's east–west width shrinks with latitude φ (section 1):

```math
\Delta y = \frac{\pi R}{2048} \approx 5.2\ \text{km}, \qquad \Delta x = \Delta y \cos\varphi
```

A cell is blocked if its slope is over 5° (so large crater rims become walls) or if |φ| > 80° (polar caps). The search cost is travel time, and A\* adds a guess of the time still to go:

```math
f(n) = g(n) + h(n), \qquad h(n) = \frac{d_{\text{gc}}(n, \text{goal})}{v_{\max}}
```

g(n) is the time already driven, d\_gc the great-circle (haversine, section 2) distance and v\_max = 12 km/h. Because no cell is ever faster than 12 km/h (every speed factor below is ≤ 1), h never over-estimates, so A\* still returns the fastest path — it just looks at far fewer cells than Dijkstra would.

**Why 16 directions.** On a grid a path can only move in the allowed directions, so a straight line at an awkward angle becomes a zig-zag. The worst case is a line halfway between two allowed directions α and β:

```math
\frac{L_{\text{grid}}}{L_{\text{true}}} = \frac{\sin(\beta-\theta) + \sin(\theta-\alpha)}{\sin(\beta-\alpha)}
```

With 8 directions (0°, 45°, …) the worst is θ = 22.5°: 2 sin 22.5° / sin 45° = 1.082, an 8.2 % detour. Adding the 8 knight moves (angles of 26.6° and 63.4°, like a chess knight) shrinks the largest gap to 26.6°, and the worst case falls to 1.027 — under 3 %. A knight move is only allowed when both cells it cuts across are open, so it can't jump through a corner of a wall. The kinks you see on the map are this grid, not wrong terrain.

**11.2 Pass 2 — Dijkstra on the full 463 m terrain.** Each pass-1 road is cut into \~300 km pieces. Around each piece a strip of ±40 km is cut out of the full 463 m MOLA DEM (40 km ≈ 0.68° of latitude, because 1° of latitude = πR/180 ≈ 59 km on Mars). Slope per cell, with the true east–west spacing:

```math
s = \arctan\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}, \qquad \Delta x = 463\,\text{m} \cdot \cos\varphi
```

Cells over s\_max = 12° are blocked. The strip becomes a sparse graph (one node per open cell, 16 edges each) solved by SciPy's Dijkstra. Each edge weight is its length times the average cost of its two cells:

```math
w_{ab} = L_{ab} \cdot \tfrac12\,(c_a + c_b), \qquad c = \frac{1}{f_{\text{route}}(s)}
```

**Why the search ignores direction.** A graph edge is the same weight both ways, but driving up a hill is slower than driving down it. So during the search the speed factor averages the uphill and downhill rules for that slope:

```math
f_{\text{route}}(s) = \tfrac12\left[\max\!\left(0.3,\ 1-\frac{s}{s_{\max}}\right) + \max\!\left(0.5,\ 1-\frac{s}{2\,s_{\max}}\right)\right]
```

In loose dust (11.4) f\_route is halved, so the road bends around dust when the strip leaves room. Only after the path is found is it timed properly, direction by direction (11.3).

**11.3 Timing a road.** For each step of the chosen path: horizontal run d, height change Δz, true length and grade

```math
L = \sqrt{d^2 + \Delta z^2}, \qquad g = \operatorname{atan2}(\Delta z,\ d)
```

The speed factor depends on whether the step climbs or descends, and is cut again for the ground's overall slope s (a stand-in for side slope):

```math
f = \begin{cases} \max\!\left(0.3,\ 1 - \dfrac{g}{s_{\max}}\right) & g > 0 \ \text{(uphill)} \\[6pt] \max\!\left(0.5,\ 1 - \dfrac{|g|}{2\,s_{\max}}\right) & g \le 0 \ \text{(downhill)} \end{cases} \qquad f \leftarrow f \cdot \max\!\left(0.5,\ 1 - \frac{s}{2\,s_{\max}}\right)
```

```math
v = 12\ \text{km/h} \cdot f, \qquad t = \frac{L}{v}
```

**Worked example.** Driving straight up a 6° slope: uphill f = 1 − 6/12 = 0.5; slope cut = 1 − 6/24 = 0.75; f = 0.375 → v = 4.5 km/h. Straight down the same slope: f = (1 − 6/24) × 0.75 = 0.56 → 6.75 km/h. Flat ground: 12 km/h. Honest note: the slope cut uses the cell's total slope even when you drive straight up it, so pure climbs are counted a little slower than a true side-slope rule would give — a conservative simplification.

**11.4 Loose dust — TES thermal inertia.** Thermal inertia says how strongly ground resists a change in temperature:

```math
I = \sqrt{k\,\rho\,c} \qquad \left[\text{J m}^{-2}\,\text{K}^{-1}\,\text{s}^{-1/2}\right]
```

k is thermal conductivity, ρ density and c heat capacity. Loose dust is full of gaps, so it conducts heat badly (tiny k): it heats fast by day and cools fast at night — low I. Rock conducts well — high I. Illustrative values: dust with k ≈ 0.005 W m⁻¹ K⁻¹, ρ ≈ 1,300 kg m⁻³, c ≈ 800 J kg⁻¹ K⁻¹ gives I ≈ 72; solid basalt (k ≈ 2, ρ ≈ 2,900, c ≈ 800) gives I ≈ 2,150. The orbiter measures I from how fast the surface cools at night (Putzig & Mellon 2007 map, \~3 km pixels). Our classes: I < 100 soft (dust-mantled), 100–150 caution, ≥ 150 firm. Sampling every road every 2 km: 3,390 of 41,523 km is soft, 3,390 / 41,523 = 8.2 %. The scenario halves speed on soft stretches (t → 2t): Habitat 1 289 → 307 sols, Habitat 2 282 → 296 sols. The dust is measured; the half-speed is an assumption.

**11.5 Visit order — Held-Karp.** Habitat 2 must visit 7 sites and return home: the travelling-salesman problem. Held-Karp solves it exactly with dynamic programming. D(S, j) is the shortest path that starts at the habitat, visits every site in set S once and ends at site j:

```math
D(S, j) = \min_{k \in S \setminus \{j\}} \Big[ D(S \setminus \{j\},\ k) + d(k, j) \Big], \qquad \text{tour} = \min_j \big[ D(\text{all}, j) + d(j, \text{home}) \big]
```

The sets are stored as bit masks (site k in S ⇔ bit k is 1). Work grows as n² · 2ⁿ instead of n!: for 8 nodes that is 8² × 2⁸ = 16,384 steps versus 7! = 5,040 orders by brute force — both trivial here, but at 20 sites brute force needs \~10¹⁷ orders and Held-Karp \~4 × 10⁸. Distances d are great-circle (section 2), then the chosen order is driven on real roads. Habitat 1 does not use the shortest loop: its route is set by hand (out to Opportunity and back), and a site passed twice is researched only on the first visit.

**11.6 The sol-by-sol plan.** For each leg with driving time T (from 11.3) and 8 driving hours per sol:

```math
n_{\text{drive}} = \left\lceil \frac{T}{8\ \text{h}} \right\rceil, \qquad \text{total sols} = n_{\text{drive}} + n_{\text{rest}} + 5 \cdot n_{\text{sites}} + 1
```

A rest sol follows every 6 driving sols in a row; 5 research sols per site; the +1 is the arrival sol back at the habitat. Habitat 1: 209 + 34 + 45 + 1 = 289. Habitat 2: 213 + 33 + 35 + 1 = 282. A camp sits at the end of every driving sol that does not end at a site.

**Depots.** One every 800 km of road: ⌊18,499 / 800⌋ = 23 for Habitat 1, ⌊18,772 / 800⌋ = 23 for Habitat 2. Two robots per habitat leave in opposite directions at 10 km/h (crew hours × 12/10). The split point c is chosen to finish soonest:

```math
c^{*} = \arg\min_c \ \max\big(T_A(c),\ T_B(c)\big)
```

For Habitat 1 that gives 116 and 119 sols. The speed check: the farthest depot is \~9,600 km by road, the cargo-to-crew window \~600 sols, so a robot must average 9,600 / 600 = 16 km per sol, i.e. 2 km/h over 8 h. Perseverance's best sol is 412 m: 16,000 / 412 ≈ 39× short.

**11.7 Seasons and dose.** Solar longitude Ls is Mars's position around the Sun (Ls 0 = northern spring equinox). A Mars year is 668.6 sols; northern spring (194 sols) + summer (178) = 372 sols, the calm half before the dust-storm season (all recorded global storms began at Ls 180–310). Margin = 372 − route: Habitat 1 83 sols, Habitat 2 90 sols. Dose is rate × time, with 1 sol = 1.0275 Earth days:

```math
H_{\text{route}} = \dot H_{\text{surface}} \cdot n_{\text{sols}} \cdot 1.0275, \qquad \dot H_{\text{surface}} = 0.64 \pm 0.12\ \text{mSv/day}
```

Habitat 1: 0.64 × 289 × 1.0275 ≈ 190 mSv. Habitat 2: 0.64 × 282 × 1.0275 ≈ 185 mSv. Cruise (Curiosity RAD in flight, 1.84 mSv/day): 1.84 × 180 ≈ 331 mSv each way, 662 mSv for the round trip — already above NASA's 600 mSv career limit before anyone sets foot on Mars.

## 12. Quick reference

The constants and formulas from this doc on one page, for looking up during the build.

| Constant | Value |
| --- | --- |
| Mars sphere radius R | 3,396,190 m |
| Metres per degree on Mars | 59,274 m |
| Mars gravity g | 3.71 m/s² (0.378 of Earth's 9.81) |
| Sol length | 24 h 39 min 35 s |
| Leaflet's Earth radius | 6,371,000 m (circle factor 1.876) |
| DTM pixel / ortho pixel | 1.0117 m / 0.253 m |
| DTM accuracy | ±1.3 m vertical, ±100 m horizontal |
| Suited astronaut on Mars | 746 N (80 kg + 121 kg suit) |
| GCR dose at Gale | 0.67 mSv per day |

| Formula | Use |
| --- | --- |
| x = Rλ, y = Rφ | Degrees ↔ metres on the DTM grid |
| d = 2R arcsin √a | Great-circle distance (haversine) |
| D = 180° / 2^z | Tile size at zoom z |
| z\* = log₂(180 / (256Δ)) | Native zoom for pixel size Δ in degrees |
| slope = arctan √(p² + q²) | Slope from Horn gradients p, q |
| δθ ≈ arctan(σ / L) | Slope error over baseline L |
| SE(r) ≈ (1 − r²) / √(n − 1) | Uncertainty of a correlation |
| \|∇T\| = 1 / F | Eikonal equation for travel time |
| Fr = v² / (gL) | Froude number; walk–run at 0.5 |
| v(θ) = v\_flat × C(0) / C(θ) | Constant-effort walking speed |
| cos(tilt) = cos(roll) cos(pitch) | Rover tilt from attitude |
| SVF = 1 − mean(sin hₖ) | Open-sky fraction for shielding |

**Sources**

- [Minetti et al. 2002, energy cost of walking at extreme slopes](https://iris.unibs.it/retrieve/ddc633e4-3c03-4e2e-e053-3705fe0a4c80/Minetti%20JAP%202002.pdf)
- [Kram, Domingo & Ferris 1997, reduced gravity and the walk–run transition](https://ntrs.nasa.gov/citations/20040173033)
- [Norcross et al. 2010, inclined walking in a planetary suit (NASA/TP-2010-216125)](https://ntrs.nasa.gov/api/citations/20110003409/downloads/Norcross%20et%20al%202010%2C%20Metabolic%20costs%20%26%20biomech%20of%20inclined%20ambulation%20%26%20exploration%20tasks%20in%20a%20planet%20suit.pdf)
- [Vos, Gernhardt & Lee 2007, 10 km walkback test](https://corpora.tika.apache.org/base/docs/govdocs1/515/515870.pdf)
- [SwRI, first radiation measurements from the surface of Mars (Hassler et al. 2014)](https://swri.org/node/9079)
- [MSL landing site engineering constraints (JPL)](https://marsoweb.nas.nasa.gov/landingsites/msl/memoranda/MSL_Eng_User_Guide_v2.pdf)
- [USGS HiRISE DTM documentation](https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/)
- [scikit-fmm (Fast Marching in Python)](https://github.com/scikit-fmm/scikit-fmm)
