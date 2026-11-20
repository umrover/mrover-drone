import os
import numpy as np
import matplotlib.pyplot as plt
from pymavlink import mavutil

tlog_path = os.path.expanduser("~/Documents/QGroundControl Daily/Telemetry/2026-11-11 22-01-42.tlog")
mlog = mavutil.mavlogfile(tlog_path)

lats, lons = [], []

while True:
    msg = mlog.recv_match(type="GPS_RAW_INT", blocking=False)
    if msg is None:
        break
    if msg.fix_type >= 5: # 3: 3D fix, 5: RTK float, 6: RTK fix
        lats.append(msg.lat / 1e7)
        lons.append(msg.lon / 1e7)

if len(lats) == 0 or len(lons) == 0:
    print("No data available")
    exit(1)

# mean is (0,0) in plot
lats, lons = np.array(lats), np.array(lons)
lat0, lon0 = lats.mean(), lons.mean()

# earth radius in meters
R = 6378137.0
# convert degree offsets from mean into meters
north_m = np.radians(lats - lat0) * R
east_m = np.radians(lons - lon0) * R * np.cos(np.radians(lat0))

# 2D euclidean distance (radius) of each GPS fix
radii = np.hypot(east_m, north_m)
cep = np.percentile(radii, 50)
r95 = np.percentile(radii, 95)

fig, ax = plt.subplots(figsize=(7,7))
ax.scatter(east_m, north_m, s=8, alpha=0.6, label=f"Fixes (n={len(radii)})")

ax.add_patch(plt.Circle((0, 0), cep, color="green", fill=False, lw=2, label=f"CEP (50%): {cep:.3f}m"))
ax.add_patch(plt.Circle((0, 0), r95, color="red", fill=False, lw=2, linestyle="--", label=f"R95 (95%): {r95:.3f}m"))

ax.axhline(0, color="gray", lw=0.5)
ax.axhline(0, color="gray", lw=0.5)
ax.set_aspect("equal", "box")
ax.set_xlabel("East error from mean (m)")
ax.set_xlabel("North error from mean (m)")
ax.set_title("Stationary GPS precision (.tlog)")
ax.legend()
ax.grid(True, linestyle=":", alpha=0.5)
plt.show()
