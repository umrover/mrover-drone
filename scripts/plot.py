from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pymavlink import mavutil

telemetry_dir = Path("~/Documents/QGroundControl Daily/Telemetry").expanduser()

output_dir = telemetry_dir / "gps_plots"
output_dir.mkdir(parents=True, exist_ok=True)

MIN_POINTS = 50
STOP_ON_TAKEOFF = False # stop collecting if drone starts flying
# earth radius in meters
R = 6378137.0

results = []

FIX_LABELS = {
    3: "3D_FIX",
    4: "DGPS",
    5: "RTK_FLOAT",
    6: "RTK_FIX",
}

tlog_files = sorted(telemetry_dir.glob("*.tlog"))
print(f"Found {len(tlog_files)} .tlog files in {telemetry_dir}\n")

for tlog_path in tlog_files:
    # store lat/lon lists separately for each fix type
    coords_by_fix = {ft: {"lats": [], "lons": []} for ft in FIX_LABELS}
    is_armed = False
    seen_vehicle_heartbeat = False
    landed_state = False

    try:
        mlog = mavutil.mavlink_connection(str(tlog_path))

        while True:
            msg = mlog.recv_match(type=["HEARTBEAT", "EXTENDED_SYS_STATE", "GPS_RAW_INT"], blocking=False)
            if msg is None:
                break

            msg_type = msg.get_type()

            if msg_type == "HEARTBEAT":
                if msg.type != mavutil.mavlink.MAV_TYPE_GCS and msg.autopilot != mavutil.mavlink.MAV_AUTOPILOT_INVALID:
                    seen_vehicle_heartbeat = True
                    is_armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

            elif msg_type == "EXTENDED_SYS_STATE":
                landed_state = msg.landed_state
                total_pts = sum(len(v["lats"]) for v in coords_by_fix.values())
                # 2=IN_AIR, 3=TAKEOFF
                if STOP_ON_TAKEOFF and landed_state in (2,3) and total_pts > 0:
                    break

            elif msg_type == "GPS_RAW_INT":
                if msg.fix_type not in FIX_LABELS:
                    continue

                if (landed_state is not None):
                    on_ground = (landed_state == 1)
                else:
                    on_ground = (seen_vehicle_heartbeat and not is_armed)
                
                # 3: 3D fix, 4: DGPS, 5: RTK float, 6: RTK fix
                if on_ground:
                    coords_by_fix[msg.fix_type]["lats"].append(msg.lat / 1e7)
                    coords_by_fix[msg.fix_type]["lons"].append(msg.lon / 1e7)
    
    except Exception as e:
        print(f"[Error] {tlog_path.name}: {e}")
        results.append({"fix": 99, "file": tlog_path.name, "fix": "-", "n": 0, "cep": "-", "r95": "-", "status": f"ERROR: {e}"})
        continue

    for fix_type, label in FIX_LABELS.items():
        lats = np.array(coords_by_fix[fix_type]["lats"])
        lons = np.array(coords_by_fix[fix_type]["lons"])

        if len(lats) < MIN_POINTS:
            print(f"[SKIP] {tlog_path.name}: only {len(lats)} disarmed fixes (need {MIN_POINTS})")
            continue

        # mean is (0,0) in plot
        lat0, lon0 = lats.mean(), lons.mean()

        # convert degree offsets from mean into meters
        north_m = np.radians(lats - lat0) * R
        east_m = np.radians(lons - lon0) * R * np.cos(np.radians(lat0))
        # 2D euclidean distance (radius) of each GPS fix
        radii = np.hypot(east_m, north_m)

        cep = np.percentile(radii, 50)
        r95 = np.percentile(radii, 95)

        if r95 < 0.5:
            scale, unit = 100.0, "cm"
        else:
            scale, unit = 1.0, "m"

        x = east_m * scale
        y = north_m * scale
        cep = cep * scale
        r95 = r95 * scale

        fig, ax = plt.subplots(figsize=(7.5,7.5))
        ax.scatter(x, y, s=18, alpha=0.6, label=f"Fixes (n={len(radii)})")

        ax.add_patch(plt.Circle((0, 0), cep, color="green", fill=False, lw=2, label=f"CEP (50%): {cep:.3f}{unit}"))
        ax.add_patch(plt.Circle((0, 0), r95, color="red", fill=False, lw=2, linestyle="--", label=f"R95 (95%): {r95:.3f}{unit}"))

        lim = max(np.max(np.abs(x)), np.max(np.abs(y)), r95, 1e-6) * 1.15
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal", "box")

        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.yaxis.set_major_locator(MaxNLocator(5))

        ax.axhline(0, color="gray", lw=0.6)
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_xlabel(f"East error from mean ({unit})")
        ax.set_ylabel(f"North error from mean ({unit})")
        ax.set_title(f"Stationary {label.replace("_"," ")} precision - {tlog_path.name}", pad=35)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.09), ncol=3, frameon=True)
        ax.grid(True, linestyle=":", alpha=0.5)

        out_file = output_dir / f"{label}_{tlog_path.stem}.png"
        fig.savefig(out_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

        results.append({
            "fix": label,
            "file": tlog_path.name,
            "n": len(radii),
            "cep": f"{cep:.2f} {unit}",
            "r95": f"{r95:.2f} {unit}",
            "status": "SAVED",
        })

        print(f"[SAVED] {out_file.name} | n={len(radii)}, CEP={cep:.3f}{unit}, R95={r95:.3f}{unit}")

# Print table header once before the loop starts
print(f"\n{'Log File':<28} | {'Fix Type':<10} | {'Points':>6} | {'CEP (50%)':>10} | {'R95 (95%)':>10} | {'Status'}")
print("-" * 86)

fix_order = {label: ft for ft, label in FIX_LABELS.items()}
for r in sorted(results, key=lambda r: (fix_order.get(r["fix"]), r["file"])):
    print(f"{r['file']:<28} | {r['fix']:<10} | {r['n']:>6} | {r['cep']:>10} | {r['r95']:>10} | {r['status']}")

saved_count = sum(1 for r in results if r["status"] == "SAVED")
print("-" * 86)
print(f"Done. Saved {saved_count} plot(s) to: {output_dir}")
