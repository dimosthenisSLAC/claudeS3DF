"""Generate plots for the simulation report as base64-encoded PNGs."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import base64
import io
import json
import os

os.makedirs(os.path.expanduser("~/claudeS3DF/results/report"), exist_ok=True)

def fig_to_base64(fig, dpi=150):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

plots = {}

# ============================================================
# 1. Cu Melting: RDF at different temperatures
# ============================================================
print("Generating Cu melting RDF plot...")
fig, ax = plt.subplots(figsize=(10, 7))
temperatures = [300, 500, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500]
cmap = plt.cm.coolwarm
colors = [cmap(i / (len(temperatures) - 1)) for i in range(len(temperatures))]

rdf_dir = os.path.expanduser("~/claudeS3DF/results/cu_melting")
for i, T in enumerate(temperatures):
    fname = os.path.join(rdf_dir, f"rdf_T{T}K.dat")
    if os.path.exists(fname):
        data = np.loadtxt(fname)
        r, g = data[:, 0], data[:, 1]
        offset = i * 1.5  # vertical offset for clarity
        ax.plot(r, g + offset, color=colors[i], linewidth=1.5,
                label=f"{T} K")
        ax.text(7.5, offset + 1.0, f"{T} K", color=colors[i],
                fontsize=9, fontweight="bold", va="center")

ax.set_xlabel("r (Å)", fontsize=13)
ax.set_ylabel("g(r) + offset", fontsize=13)
ax.set_title("Radial Distribution Function of Cu during Heating\n"
             "(CHGNet MLIP, 108 atoms, NVT Langevin MD)", fontsize=14)
ax.set_xlim(1.5, 8.5)
ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
ax.legend(loc="upper right", fontsize=8, ncol=2, framealpha=0.9)
fig.tight_layout()
plots["cu_rdf"] = fig_to_base64(fig)
fig.savefig(os.path.join(rdf_dir, "rdf_all_temperatures.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# 2. Cu Melting: Energy and RDF peak vs Temperature
# ============================================================
print("Generating Cu melting energy/order plot...")
results_data = {
    "T": [300, 500, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500],
    "E": [-4.0459, -4.0249, -3.9876, -3.9667, -3.9428, -3.9236, -3.8940, -3.8735, -3.8352, -3.8118, -3.7661],
    "RDF_peak": [6.58, 6.27, 4.52, 3.95, 3.69, 3.65, 3.54, 3.32, 3.14, 3.24, 2.97],
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(results_data["T"], results_data["E"], "o-", color="#2196F3", linewidth=2, markersize=7)
ax1.set_xlabel("Temperature (K)", fontsize=12)
ax1.set_ylabel("Energy per atom (eV)", fontsize=12)
ax1.set_title("Energy vs Temperature", fontsize=13)
ax1.axvline(x=1358, color="red", linestyle="--", alpha=0.7, label="Expt. Tm = 1358 K")
ax1.axvspan(1600, 2000, alpha=0.15, color="orange", label="CHGNet melting region")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(results_data["T"], results_data["RDF_peak"], "s-", color="#4CAF50", linewidth=2, markersize=7)
ax2.set_xlabel("Temperature (K)", fontsize=12)
ax2.set_ylabel("RDF 1st peak height g(r)", fontsize=12)
ax2.set_title("Crystalline Order Parameter", fontsize=13)
ax2.axvline(x=1358, color="red", linestyle="--", alpha=0.7, label="Expt. Tm = 1358 K")
ax2.axvspan(1600, 2000, alpha=0.15, color="orange", label="CHGNet melting region")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)

fig.suptitle("Cu Melting Simulation — CHGNet on NVIDIA A100", fontsize=14, y=1.02)
fig.tight_layout()
plots["cu_energy_order"] = fig_to_base64(fig)
fig.savefig(os.path.join(rdf_dir, "energy_and_order.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# 3. ORCA AIMD: Energy and Temperature vs time
# ============================================================
print("Generating ORCA AIMD plots...")
orca_csv = os.path.expanduser("~/claudeS3DF/results/na_water_aimd-md-ener.csv")
if os.path.exists(orca_csv):
    # Parse the CSV - ORCA uses semicolons
    with open(orca_csv) as f:
        lines = f.readlines()
    # Find header line
    header_idx = 0
    for i, line in enumerate(lines):
        if "Step" in line:
            header_idx = i
            break
    headers = [h.strip().strip('"') for h in lines[header_idx].split(";")]
    data_lines = []
    for line in lines[header_idx+1:]:
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                vals = [float(x) for x in line.split(";")]
                data_lines.append(vals)
            except ValueError:
                continue
    if data_lines:
        data = np.array(data_lines)
        step = data[:, 0]
        time_fs = data[:, 1]

        # Find columns
        col_map = {h: i for i, h in enumerate(headers)}
        temp_col = None
        epot_col = None
        etot_col = None
        for h, i in col_map.items():
            if "Temp" in h:
                temp_col = i
            if "E_pot" in h or "EPot" in h or "Pot" in h:
                epot_col = i
            if "E_tot" in h or "ETot" in h or "Total" in h:
                etot_col = i

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

        # Temperature
        if temp_col is not None:
            temp = data[:, temp_col]
            ax1.plot(time_fs, temp, color="#E91E63", linewidth=0.8, alpha=0.8)
            ax1.axhline(y=300, color="blue", linestyle="--", alpha=0.5, label="Target: 300 K")
            ax1.set_ylabel("Temperature (K)", fontsize=12)
            ax1.set_title("ORCA AIMD: Na⁺ in 10 H₂O (r²SCAN-3c DFT)", fontsize=14)
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3)

        # Potential energy
        if epot_col is not None:
            epot = data[:, epot_col] * 27.2114  # Hartree to eV
            ax2.plot(time_fs, epot, color="#3F51B5", linewidth=0.8, alpha=0.8)
            ax2.set_ylabel("Potential Energy (eV)", fontsize=12)
            ax2.set_xlabel("Time (fs)", fontsize=12)
            ax2.grid(True, alpha=0.3)
        elif etot_col is not None:
            etot = data[:, etot_col] * 27.2114
            ax2.plot(time_fs, etot, color="#3F51B5", linewidth=0.8, alpha=0.8)
            ax2.set_ylabel("Total Energy (eV)", fontsize=12)
            ax2.set_xlabel("Time (fs)", fontsize=12)
            ax2.grid(True, alpha=0.3)

        fig.tight_layout()
        plots["orca_md"] = fig_to_base64(fig)
        fig.savefig(os.path.expanduser("~/claudeS3DF/results/report/orca_aimd.png"),
                    dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"  Parsed {len(data_lines)} steps, columns: {headers}")
else:
    print("  ORCA CSV not found, skipping")

# ============================================================
# 4. Performance comparison bar chart
# ============================================================
print("Generating performance comparison...")
fig, ax = plt.subplots(figsize=(8, 5))

methods = ["CHGNet\n(A100 GPU)", "ORCA r²SCAN-3c\n(1 CPU core)"]
ms_per_step = [92, 19200]  # ms
atoms = [108, 31]
colors_bar = ["#4CAF50", "#FF9800"]

bars = ax.bar(methods, ms_per_step, color=colors_bar, width=0.5, edgecolor="black", linewidth=0.5)
ax.set_ylabel("Time per MD step (ms)", fontsize=12)
ax.set_title("Performance: MLIP vs DFT for Molecular Dynamics", fontsize=13)
ax.set_yscale("log")
ax.set_ylim(10, 100000)

for bar, n in zip(bars, atoms):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3,
            f"{n} atoms", ha="center", fontsize=10, fontweight="bold")

ax.text(0.5, 0.85, f"CHGNet is ~{ms_per_step[1]//ms_per_step[0]}× faster per step",
        transform=ax.transAxes, fontsize=13, ha="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9))
ax.grid(True, alpha=0.3, axis="y")
fig.tight_layout()
plots["performance"] = fig_to_base64(fig)
fig.savefig(os.path.expanduser("~/claudeS3DF/results/report/performance.png"),
            dpi=150, bbox_inches="tight")
plt.close(fig)

# ============================================================
# Save all base64 images to JSON for the HTML generator
# ============================================================
output_path = os.path.expanduser("~/claudeS3DF/results/report/plots.json")
with open(output_path, "w") as f:
    json.dump(plots, f)

print(f"\nSaved {len(plots)} plots to {output_path}")
print("Keys:", list(plots.keys()))
print("Done!")
