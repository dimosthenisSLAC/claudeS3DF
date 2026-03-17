#!/usr/bin/env python3
"""Compare OCEAN IrO2 Ir L-edge XAS spectra: S3DF vs Oscar's NERSC reference."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import glob

# Directories
oscar_dir = os.path.expanduser("~/IrO2_example/Oscar_Output")
s3df_310_dir = os.path.expanduser("~/claudeS3DF/results/ocean_iro2_3.1.0/spectra")
s3df_321_dir = os.path.expanduser("~/claudeS3DF/results/ocean_iro2_3.2.0.1/spectra")
out_dir = os.path.expanduser("~/claudeS3DF/results")

# L-edge labels: 2p_01 = L3 (2p3/2), 2p_02 = L2 (2p1/2), 2p_03 = L1 (2s)
# Actually for Ir: edges{ -77 2 1 } means n=2, l=1 (2p)
# 2p_01 = first 2p subshell, 2p_02 = second, 2p_03 = third polarization
# For IrO2 with 2 Ir atoms: 0001 and 0002 are the two inequivalent Ir sites
edge_labels = {
    '2p_01': 'L₃ (pol 1)',
    '2p_02': 'L₃ (pol 2)',
    '2p_03': 'L₃ (pol 3)',
}

def load_spectrum(filepath):
    """Load OCEAN absspct file, return energy (eV) and spectral intensity."""
    data = np.loadtxt(filepath, comments='#')
    energy = data[:, 0]  # eV relative to edge
    spect = data[:, 1]   # spectral function
    return energy, spect

def sum_sites(directory, edge_suffix):
    """Sum spectra over both Ir sites for a given edge/polarization."""
    f1 = os.path.join(directory, f"absspct_Ir.0001_{edge_suffix}")
    f2 = os.path.join(directory, f"absspct_Ir.0002_{edge_suffix}")
    e1, s1 = load_spectrum(f1)
    e2, s2 = load_spectrum(f2)
    return e1, s1 + s2

def isotropic_average(directory):
    """Compute isotropic average (sum over 3 polarizations, both sites, divide by 3)."""
    total = None
    energy = None
    for pol in ['2p_01', '2p_02', '2p_03']:
        e, s = sum_sites(directory, pol)
        if total is None:
            energy = e
            total = s.copy()
        else:
            total += s
    return energy, total / 3.0

# ============================================================
# Figure 1: Isotropic average comparison
# ============================================================
fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})

# Load isotropic averages
oscar_e, oscar_s = isotropic_average(oscar_dir)

has_310 = os.path.exists(os.path.join(s3df_310_dir, "absspct_Ir.0001_2p_01"))
has_321 = os.path.exists(os.path.join(s3df_321_dir, "absspct_Ir.0001_2p_01"))

# Plot main spectra
ax = axes[0]
ax.plot(oscar_e, oscar_s, 'k-', lw=2, label='Oscar (NERSC)', alpha=0.8)

if has_321:
    s3df_321_e, s3df_321_s = isotropic_average(s3df_321_dir)
    ax.plot(s3df_321_e, s3df_321_s, 'r--', lw=1.5, label='S3DF OCEAN 3.2.0.1')

if has_310:
    s3df_310_e, s3df_310_s = isotropic_average(s3df_310_dir)
    ax.plot(s3df_310_e, s3df_310_s, 'b:', lw=1.5, label='S3DF OCEAN 3.1.0')

# Auto-detect plot range: focus on the main spectral features
peak_idx = np.argmax(oscar_s)
peak_e = oscar_e[peak_idx]
plot_min = peak_e - 40
plot_max = peak_e + 80
mask_plot = (oscar_e >= plot_min) & (oscar_e <= plot_max)

ax.set_xlim(plot_min, plot_max)
ax.set_ylabel('Absorption (arb. units)', fontsize=12)
ax.set_title('IrO₂ Ir L-edge XANES — OCEAN BSE\nS3DF (Milano/QE 7.3/OpenBLAS) vs NERSC Reference', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Plot difference
ax2 = axes[1]
if has_321:
    diff_321 = s3df_321_s - oscar_s
    max_signal = np.max(np.abs(oscar_s[mask_plot]))
    rel_diff_321 = diff_321 / max_signal * 100
    ax2.plot(oscar_e, rel_diff_321, 'r-', lw=1, label='3.2.0.1 − Oscar (% of max)')
    rms = np.sqrt(np.mean(rel_diff_321[mask_plot]**2))
    ax2.text(0.02, 0.85, f'RMS diff: {rms:.3f}%', transform=ax2.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

if has_310:
    diff_310 = s3df_310_s - oscar_s
    rel_diff_310 = diff_310 / max_signal * 100
    ax2.plot(oscar_e, rel_diff_310, 'b-', lw=1, label='3.1.0 − Oscar (% of max)')

ax2.set_xlim(plot_min, plot_max)
ax2.set_xlabel('Energy (eV)', fontsize=12)
ax2.set_ylabel('Difference (%)', fontsize=12)
ax2.axhline(0, color='k', lw=0.5)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'ocean_iro2_comparison.png'), dpi=150)
print(f"Saved: {os.path.join(out_dir, 'ocean_iro2_comparison.png')}")

# ============================================================
# Figure 2: Per-polarization comparison
# ============================================================
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

for i, (suffix, label) in enumerate(edge_labels.items()):
    ax = axes2[i]
    e_o, s_o = sum_sites(oscar_dir, suffix)
    ax.plot(e_o, s_o, 'k-', lw=2, label='Oscar (NERSC)')

    if has_321:
        e_s, s_s = sum_sites(s3df_321_dir, suffix)
        ax.plot(e_s, s_s, 'r--', lw=1.5, label='S3DF 3.2.0.1')

    if has_310:
        e_s, s_s = sum_sites(s3df_310_dir, suffix)
        ax.plot(e_s, s_s, 'b:', lw=1.5, label='S3DF 3.1.0')

    ax.set_xlim(plot_min, plot_max)
    ax.set_xlabel('Energy (eV)', fontsize=11)
    ax.set_title(label, fontsize=12)
    ax.grid(True, alpha=0.3)
    if i == 0:
        ax.set_ylabel('Absorption (arb. units)', fontsize=11)
    if i == 2:
        ax.legend(fontsize=9)

fig2.suptitle('IrO₂ Ir L-edge — Per-Polarization Comparison', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'ocean_iro2_polarizations.png'), dpi=150)
print(f"Saved: {os.path.join(out_dir, 'ocean_iro2_polarizations.png')}")

# Print numerical comparison
print("\n=== Numerical Comparison ===")
if has_321:
    mask = mask_plot
    max_s = np.max(oscar_s[mask])
    diff = np.abs(s3df_321_s - oscar_s)
    print(f"OCEAN 3.2.0.1 vs Oscar:")
    print(f"  Max absolute diff:  {np.max(diff[mask]):.6e}")
    print(f"  RMS absolute diff:  {np.sqrt(np.mean(diff[mask]**2)):.6e}")
    print(f"  Max relative diff:  {np.max(diff[mask])/max_s*100:.4f}%")
    print(f"  RMS relative diff:  {np.sqrt(np.mean((diff[mask]/max_s*100)**2)):.4f}%")

    # Find peak position
    peak_idx_oscar = np.argmax(oscar_s[mask])
    peak_idx_s3df = np.argmax(s3df_321_s[mask])
    e_mask = oscar_e[mask]
    print(f"  Oscar peak at:      {e_mask[peak_idx_oscar]:.2f} eV")
    print(f"  S3DF peak at:       {e_mask[peak_idx_s3df]:.2f} eV")
    print(f"  Peak shift:         {e_mask[peak_idx_s3df] - e_mask[peak_idx_oscar]:.2f} eV")
