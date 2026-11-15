#!/usr/bin/env bash
# MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
# Habitat 1 v5: no Phoenix -> Opportunity road; new Phoenix -> Chryse road; Opportunity is an out-and-back spur.
# Re-routes all 13 H1 legs on MOLA 463 m (road463.py) and measures loose dust on them (ti_roads.py).
set -e
W=~/SpaceApps2026/work
cd "$W/layers"
DEM=$(find "$W" -name 'mola_463m.tif' | head -1)
TI=$(find "$W" -iname '*.img' | grep -iE 'ti|mgst|night' | head -1)
echo "DEM: $DEM"; echo "TI:  $TI"
[ -f "$DEM" ] && [ -f "$TI" ] || { echo "missing DEM or TI file"; exit 1; }
mv -f ~/Downloads/points_h1_v5.json "$W/layers/" 2>/dev/null || true
ONLY=$(seq -s, -f 'H1-%g' 1 13)
python3 road463.py --dem "$DEM" --points points_h1_v5.json --ti "$TI" --out r463_h1v5 --only "$ONLY"
python3 - <<'EOF'
import json
P = json.load(open('points_h1_v5.json')); G = json.load(open('r463_h1v5/legs_463.geojson'))
roads = [dict(region=f['properties']['region'], leg=f['properties']['leg'], frm=f['properties']['frm'], to=f['properties']['to'],
              road_km=f['properties']['road_km'], geo=f['geometry']['coordinates']) for f in G['features']]
json.dump({'sites': P['sites'], 'roads': roads}, open('points_h1_v5_routed.json', 'w'))
print('routed legs:', len(roads))
EOF
python3 ti_roads.py --img "$TI" --points points_h1_v5_routed.json --out ti_h1v5
cd "$W/layers" && rm -f ~/SpaceApps2026/work/h1v5.zip && zip -qr ~/SpaceApps2026/work/h1v5.zip r463_h1v5 ti_h1v5 points_h1_v5_routed.json
ls -la ~/SpaceApps2026/work/h1v5.zip
echo "DONE - upload ~/SpaceApps2026/work/h1v5.zip"
