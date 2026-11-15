"""Cut a Mars COG (IAU eqc, lat_ts 0) into Leaflet EPSG4326 tiles: OUT/{z}/{x}/{y}.png
MartianAutonomy | NASA Space Apps 2026 | Made with AI assistance (Claude)
usage: python3 make_tiles.py URL OUT_DIR ZMIN ZMAX"""
import math, os, sys, threading, time
import numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("VSI_CACHE", "TRUE")
R, T = 3396190.0, 256
URL, OUT, ZMIN, ZMAX = sys.argv[1], os.path.expanduser(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
d2m = lambda d: math.radians(d) * R
m2d = lambda m: math.degrees(m / R)

with rasterio.open(URL) as src:
    b, n_b, res = src.bounds, src.count, src.res[0]
    oh = 1024; ow = max(1, round(oh * src.width / src.height))
    ov = src.read(out_shape=(n_b, oh, ow), resampling=Resampling.average).astype("float32")
    om = src.read_masks(1, out_shape=(oh, ow)) > 0
bands = [0, 1, 2] if n_b >= 3 else [0]
stretch = [np.percentile(ov[i][om], [1, 99]) for i in bands]
W, E, S, N = m2d(b.left), m2d(b.right), m2d(b.bottom), m2d(b.top)
native = math.log2(180 / (T * m2d(res)))
print(f"bands {n_b} | {res:.3f} m/px | native zoom {native:.2f} | "
      f"bounds {S:.4f},{W:.4f} .. {N:.4f},{E:.4f}", flush=True)

tl = threading.local()
def ds():
    if not hasattr(tl, "src"):
        tl.src = rasterio.open(URL)
    return tl.src

def tile(z, x, y):
    D = 180 / 2 ** z
    lon_l, lat_t = -180 + x * D, 90 - y * D
    src = ds()
    win = from_bounds(d2m(lon_l), d2m(lat_t - D), d2m(lon_l + D), d2m(lat_t), transform=src.transform)
    rs = Resampling.average if z < native else Resampling.bilinear
    valid = src.read_masks(1, window=win, out_shape=(T, T), boundless=True,
                           resampling=Resampling.nearest) > 0
    if not valid.any():
        return 0
    data = src.read([i + 1 for i in bands], window=win, out_shape=(len(bands), T, T),
                    boundless=True, fill_value=0, resampling=rs).astype("float32")
    chans = [np.clip((data[k] - lo) / (hi - lo) * 255, 0, 255).astype("uint8")
             for k, (lo, hi) in enumerate(stretch)]
    alpha = np.where(valid, 255, 0).astype("uint8")
    mode = "LA" if len(chans) == 1 else "RGBA"
    os.makedirs(f"{OUT}/{z}/{x}", exist_ok=True)
    Image.fromarray(np.dstack(chans + [alpha]), mode).save(f"{OUT}/{z}/{x}/{y}.png", optimize=True)
    return 1

for z in range(ZMIN, ZMAX + 1):
    D = 180 / 2 ** z
    xs = range(math.floor((W + 180) / D), math.floor((E + 180) / D) + 1)
    ys = range(math.floor((90 - N) / D), math.floor((90 - S) / D) + 1)
    jobs = [(z, x, y) for x in xs for y in ys]
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex:
        made = sum(ex.map(lambda j: tile(*j), jobs))
    print(f"z{z}: {made} tiles of {len(jobs)} candidates in {time.time()-t0:.0f}s", flush=True)

mb = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs) / 1e6
print(f"done -> {OUT}  ({mb:.0f} MB)")
