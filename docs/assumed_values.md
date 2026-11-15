# Martian Map — Researched Values (Nov 13, 2026)

Values for `config.py`. Every value carries one of three labels:
- **measured** — checked against Curiosity telemetry (rover)
- **modelled from published data** — real inputs combined into a model that cannot be tested on Mars yet (astronaut, radiation shielding)
- **proxy** — real NASA criteria written for a different purpose (habitat)

## Rover (measured — Curiosity telemetry vs DTEEC_019698_1750_019988_1750_U01)
Validation re-run Nov 13 on CLEAN waypoints: 608 of 690 that sit on valid DTM pixels and
>= ~37 m inside the data edge. (The first run included 71 waypoints on no-data that the
script had filled with the mean elevation — its "25 m wins, r = +0.184" and "+41 m offset"
were contaminated and are withdrawn.)

- Correlation DTM slope vs rover tilt: weak but real at every baseline, r = 0.13–0.15 (n = 608).
  Differences between baselines (<= 0.023) are below the uncertainty (~±0.04) → correlation
  cannot select a baseline.
- Baseline chosen by DISTRIBUTION MATCH: 25 m. DTM slope at waypoints mean 10.2° = rover tilt
  mean 10.2°; p95 21.1° vs rover 18.5° (reads slightly steeper → errs conservative).
  51 m matches the tail (p95 18.4°) but under-reads the mean (9.6°).
- Rover limits IN DTM-SLOPE UNITS (quantile-matched, 25 m baseline, at the 608 waypoints):
  - soft limit 21.1° (p95 of DTM slope where Curiosity drove)
  - hard limit 31.6° (p99). Max 43.1° rejected: single point, rover tilt never exceeded
    29.1°, so it reflects DTM/registration error, not drivable ground.
- Rover tilt itself (all 690, telemetry, DTM-independent): mean 10.0°, p95 18.8°, max 29.1°.
- DTM minus rover elevation: +27.3 m (σ 6.7 m, n = 608), unexplained → limits panel.
- Pace (rover_speed.py, sols 1930–5070): median 23.5 m per driving sol, p95 58.4 m, max 106.1 m
- Drove on 22 % of sols → mission pace 6.5 m per elapsed sol (odometry includes drives outside the DTM during 7 gaps)
- One end-of-drive waypoint per sol (all drive_type = final); pace is set by operations, not terrain

## Astronaut in suit (modelled from published data, not validated on Mars — see astronaut_walk.py)
- Suit 121 kg (NASA MKIII + PLSS mock-up), body 80 kg → 746 N on Mars (0.95 × Earth body weight)
- Flat speed 0.61 m/s (Froude-scaled; NASA suited tests used 0.56–0.97 m/s)
- Soft slope limit 16.7° (30 % grade, NASA suited test edge); hard 24.2° (45 %, human data edge)
- Walk-back distance 10 km (Apollo-based assumption, Vos et al. 2007) → 4.5 h on flat ground
- Not modelled: suit stiffness (SUIT_PENALTY = 1.0), loping gait, extra effort uphill

## Habitat (proxy — NASA lander criteria used for habitat siting)
- ≤ 15° over ~5 m; ≤ 5° over 200–500 m (MSL Landing Site Engineering Constraints, JPL)
- Landing site 100 m diameter; 1 km plume hazard radius (Hoffman/Bussey, NASA 2016)

## Radiation (baseline measured at Gale, single point; terrain shielding is modelled)
- 0.67 mSv/day GCR dose equivalent, Aug 2012–Jun 2013, solar maximum
- Hassler et al. 2014, Science 343(6169), doi:10.1126/science.1244797

## Sources
- Minetti et al. 2002, J Appl Physiol 93:1039, doi:10.1152/japplphysiol.01177.2001
- Kram, Domingo & Ferris 1997, J Exp Biol 200:821
- Norcross et al. 2010, NASA/TP-2010-216125 (inclined ambulation in a planetary suit)
- Vos, Gernhardt & Lee 2007, ICES 2007-01-3133 (10 km walkback test)
- MSL Landing Site Selection: User's Guide to Engineering Constraints (JPL)
- Hoffman & Bussey 2016, NASA NTRS 20160002369
- Hassler et al. 2014, Science 343(6169)

Made with AI assistance (Claude).
