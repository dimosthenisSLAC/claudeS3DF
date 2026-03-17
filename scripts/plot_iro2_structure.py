#!/usr/bin/env python3
"""3D visualization of the IrO2 rutile structure used in OCEAN calculations."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import os

# IrO2 rutile structure from OCEAN input (Bohr → Angstrom)
bohr_to_ang = 0.529177
acell_bohr = np.array([8.578770824150515, 8.578770824150515, 6.024768055978138])
acell_ang = acell_bohr * bohr_to_ang

# Lattice vectors (orthorhombic, rprim = identity)
a1 = np.array([acell_ang[0], 0, 0])
a2 = np.array([0, acell_ang[1], 0])
a3 = np.array([0, 0, acell_ang[2]])

# Fractional coordinates
xred = np.array([
    [0.000000000, 0.000000000, 0.000000000],  # Ir1
    [0.500000000, 0.500000000, 0.500000000],  # Ir2
    [0.308510005, 0.308510005, 0.000000000],  # O1
    [0.691489995, 0.691489995, 0.000000000],  # O2
    [0.191479996, 0.808520019, 0.500000000],  # O3
    [0.808520019, 0.191479996, 0.500000000],  # O4
])
species = ['Ir', 'Ir', 'O', 'O', 'O', 'O']

# Convert to Cartesian
cart = np.zeros_like(xred)
for i in range(len(xred)):
    cart[i] = xred[i, 0] * a1 + xred[i, 1] * a2 + xred[i, 2] * a3

# Generate supercell (2x2x2) for better visualization
supercell_atoms = []
supercell_species = []
for ix in range(-1, 2):
    for iy in range(-1, 2):
        for iz in range(-1, 2):
            shift = ix * a1 + iy * a2 + iz * a3
            for i in range(len(cart)):
                pos = cart[i] + shift
                supercell_atoms.append(pos)
                supercell_species.append(species[i])

supercell_atoms = np.array(supercell_atoms)

# Filter to show 1.5 unit cells in each direction
margin = 0.3  # Angstrom
mask = (
    (supercell_atoms[:, 0] > -margin) & (supercell_atoms[:, 0] < acell_ang[0] + margin) &
    (supercell_atoms[:, 1] > -margin) & (supercell_atoms[:, 1] < acell_ang[1] + margin) &
    (supercell_atoms[:, 2] > -margin) & (supercell_atoms[:, 2] < acell_ang[2] + margin)
)
vis_atoms = supercell_atoms[mask]
vis_species = [supercell_species[i] for i in range(len(supercell_species)) if mask[i]]

# Separate Ir and O
ir_mask = [s == 'Ir' for s in vis_species]
o_mask = [s == 'O' for s in vis_species]
ir_pos = vis_atoms[ir_mask]
o_pos = vis_atoms[o_mask]

# Find Ir-O bonds (cutoff ~2.1 Å for rutile IrO2)
bond_cutoff = 2.15
bonds = []
for i, ir in enumerate(ir_pos):
    for j, o in enumerate(o_pos):
        d = np.linalg.norm(ir - o)
        if d < bond_cutoff:
            bonds.append((ir, o))

# ============================================================
# Create 3D plot
# ============================================================
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# Plot atoms
ax.scatter(*ir_pos.T, c='#4169E1', s=400, edgecolors='black', linewidth=1.5,
           label=f'Ir (Z=77)', alpha=0.95, depthshade=True, zorder=5)
ax.scatter(*o_pos.T, c='#FF4444', s=150, edgecolors='darkred', linewidth=1,
           label='O', alpha=0.9, depthshade=True, zorder=4)

# Plot bonds
for ir, o in bonds:
    ax.plot([ir[0], o[0]], [ir[1], o[1]], [ir[2], o[2]],
            'gray', lw=1.5, alpha=0.6, zorder=1)

# Draw unit cell edges
corners = np.array([
    [0, 0, 0], a1, a2, a3,
    a1 + a2, a1 + a3, a2 + a3,
    a1 + a2 + a3
])
edges = [
    (0, 1), (0, 2), (0, 3),
    (1, 4), (1, 5),
    (2, 4), (2, 6),
    (3, 5), (3, 6),
    (4, 7), (5, 7), (6, 7)
]
for i, j in edges:
    ax.plot(*zip(corners[i], corners[j]), 'k-', lw=1.0, alpha=0.4)

# Labels and formatting
ax.set_xlabel('x (Å)', fontsize=12, labelpad=10)
ax.set_ylabel('y (Å)', fontsize=12, labelpad=10)
ax.set_zlabel('z (Å)', fontsize=12, labelpad=10)
ax.set_title('IrO₂ Rutile Structure\n'
             f'a = b = {acell_ang[0]:.3f} Å, c = {acell_ang[2]:.3f} Å  (P4₂/mnm)',
             fontsize=14, pad=20)
ax.legend(fontsize=12, loc='upper left')

# Set equal aspect ratio
max_range = max(acell_ang) * 0.6
mid = acell_ang / 2
ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

# Nice viewing angle
ax.view_init(elev=20, azim=35)

plt.tight_layout()
out_path = os.path.expanduser('~/claudeS3DF/results/iro2_structure_3d.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved: {out_path}")

# ============================================================
# Print structure summary
# ============================================================
print(f"\n=== IrO₂ Structure Summary ===")
print(f"Space group: P4₂/mnm (rutile)")
print(f"a = b = {acell_ang[0]:.4f} Å ({acell_bohr[0]:.4f} Bohr)")
print(f"c = {acell_ang[2]:.4f} Å ({acell_bohr[2]:.4f} Bohr)")
print(f"c/a = {acell_ang[2]/acell_ang[0]:.4f}")
print(f"Volume = {np.prod(acell_ang):.2f} ų")
print(f"\nAtoms ({len(species)} in unit cell):")
for i, (s, x) in enumerate(zip(species, xred)):
    c = cart[i]
    print(f"  {s:>2s}  frac: ({x[0]:.6f}, {x[1]:.6f}, {x[2]:.6f})  "
          f"cart: ({c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f}) Å")

# Bond analysis
print(f"\nIr-O bonds (cutoff {bond_cutoff} Å):")
for i in range(2):  # Only unit cell Ir atoms
    ir = cart[i]
    dists = []
    for j in range(len(o_pos)):
        d = np.linalg.norm(ir - o_pos[j])
        if d < bond_cutoff:
            dists.append(d)
    dists.sort()
    print(f"  Ir{i+1}: {len(dists)} bonds, distances: {', '.join(f'{d:.3f}' for d in dists)} Å")
