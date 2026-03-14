"""
Copper Melting Simulation with CHGNet on GPU
=============================================
- 4x4x4 FCC Cu supercell (256 atoms)
- NVT MD: ramp from 300 K to 2500 K in stages
- Compute RDF at each temperature to track solid → liquid transition
- Save full trajectory for visualization
"""

import time
import numpy as np
from ase.build import bulk
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.md.langevin import Langevin
from ase import units
from ase.io import write
from ase.io.trajectory import Trajectory

# CHGNet setup
print("Loading CHGNet on GPU...")
t0 = time.time()
from chgnet.model.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator

model = CHGNet.load()
calc = CHGNetCalculator(model=model, use_device="cuda")
print(f"CHGNet loaded in {time.time()-t0:.1f}s")
print(f"Parameters: {sum(p.numel() for p in model.parameters())/1e6:.1f}M")

# Build 4x4x4 FCC Cu supercell
atoms = bulk("Cu", "fcc", a=3.615, cubic=True) * (3, 3, 3)  # 108 atoms
atoms.calc = calc
print(f"\nSystem: {atoms.get_chemical_formula()} ({len(atoms)} atoms)")
print(f"Cell: {atoms.cell.lengths()}")
print(f"Initial energy: {atoms.get_potential_energy():.4f} eV")
print(f"Energy/atom: {atoms.get_potential_energy()/len(atoms):.4f} eV/atom")

# Temperature schedule: equilibrate then ramp
temperatures = [300, 500, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500]
equil_steps = 200    # equilibration at each T
prod_steps = 300     # production at each T (for RDF collection)
dt = 2.0  # fs - timestep

print(f"\n{'='*60}")
print(f"MD Parameters:")
print(f"  Timestep: {dt} fs")
print(f"  Temperatures: {temperatures[0]} - {temperatures[-1]} K")
print(f"  Equilibration: {equil_steps} steps per T")
print(f"  Production: {prod_steps} steps per T")
print(f"  Total steps: {len(temperatures) * (equil_steps + prod_steps)}")
print(f"{'='*60}\n")


def compute_rdf(atoms, rmax=8.0, nbins=100):
    """Compute radial distribution function."""
    positions = atoms.get_positions()
    cell = atoms.get_cell()
    n = len(atoms)

    dr = rmax / nbins
    hist = np.zeros(nbins)

    for i in range(n):
        for j in range(i+1, n):
            d = positions[j] - positions[i]
            # Minimum image convention
            d = d - np.round(d @ np.linalg.inv(cell)) @ cell
            r = np.linalg.norm(d)
            if r < rmax:
                bin_idx = int(r / dr)
                if bin_idx < nbins:
                    hist[bin_idx] += 2  # count both i-j and j-i

    # Normalize
    volume = atoms.get_volume()
    rho = n / volume
    r_edges = np.linspace(0, rmax, nbins + 1)
    r_centers = 0.5 * (r_edges[:-1] + r_edges[1:])
    shell_volumes = (4/3) * np.pi * (r_edges[1:]**3 - r_edges[:-1]**3)

    g_r = hist / (n * rho * shell_volumes)
    return r_centers, g_r


# Open trajectory file
traj = Trajectory("cu_melting.traj", "w")

# Store results
results = []

for temp in temperatures:
    print(f"\n--- T = {temp} K ---")
    t_start = time.time()

    # Set up Langevin thermostat
    MaxwellBoltzmannDistribution(atoms, temperature_K=temp)
    dyn = Langevin(atoms, timestep=dt * units.fs, temperature_K=temp,
                   friction=0.01 / units.fs)

    # Equilibration
    print(f"  Equilibrating ({equil_steps} steps)...", end=" ", flush=True)
    dyn.run(equil_steps)
    print(f"done")

    # Production - collect RDF and energies
    print(f"  Production ({prod_steps} steps)...", end=" ", flush=True)
    energies = []
    temps_actual = []

    def collect_data(a=atoms):
        e = a.get_potential_energy() / len(a)
        t = a.get_kinetic_energy() / (1.5 * units.kB * len(a))
        energies.append(e)
        temps_actual.append(t)

    # Collect every 10 steps
    dyn.attach(collect_data, interval=10)
    # Save trajectory every 20 steps
    dyn.attach(lambda: traj.write(atoms), interval=20)

    dyn.run(prod_steps)
    print(f"done")

    # Compute RDF from final snapshot
    r, g = compute_rdf(atoms)

    # Statistics
    e_mean = np.mean(energies)
    e_std = np.std(energies)
    t_mean = np.mean(temps_actual)
    elapsed = time.time() - t_start

    # First peak height (crystallinity indicator)
    peak_idx = np.argmax(g[5:]) + 5  # skip first few bins
    peak_height = g[peak_idx]
    peak_pos = r[peak_idx]

    results.append({
        "T_target": temp,
        "T_actual": t_mean,
        "E_per_atom": e_mean,
        "E_std": e_std,
        "RDF_peak": peak_height,
        "RDF_peak_pos": peak_pos,
        "time_s": elapsed,
    })

    print(f"  T_actual = {t_mean:.0f} K")
    print(f"  E/atom = {e_mean:.4f} ± {e_std:.4f} eV")
    print(f"  RDF 1st peak: g(r={peak_pos:.2f}) = {peak_height:.2f}")
    print(f"  Wall time: {elapsed:.1f}s ({elapsed/(equil_steps+prod_steps)*1000:.1f} ms/step)")

    # Save RDF data
    np.savetxt(f"rdf_T{temp}K.dat", np.column_stack([r, g]),
               header=f"r(Ang) g(r) at T={temp}K", fmt="%.4f")

traj.close()

# Write final trajectory as XYZ for easy viewing
write("cu_melting_final.xyz", atoms)

# Summary table
print(f"\n{'='*80}")
print(f"{'T_target':>8s} {'T_actual':>8s} {'E/atom':>10s} {'E_std':>8s} {'RDF_peak':>10s} {'peak_r':>8s} {'time':>8s}")
print(f"{'(K)':>8s} {'(K)':>8s} {'(eV)':>10s} {'(eV)':>8s} {'g(r)':>10s} {'(Å)':>8s} {'(s)':>8s}")
print("-" * 80)
for r in results:
    print(f"{r['T_target']:8.0f} {r['T_actual']:8.0f} {r['E_per_atom']:10.4f} {r['E_std']:8.4f} "
          f"{r['RDF_peak']:10.2f} {r['RDF_peak_pos']:8.2f} {r['time_s']:8.1f}")
print("=" * 80)

# Identify melting point (where RDF first peak drops significantly)
rdf_peaks = [r["RDF_peak"] for r in results]
for i in range(1, len(rdf_peaks)):
    if rdf_peaks[i] < 0.5 * rdf_peaks[0]:
        print(f"\nMelting transition detected between {results[i-1]['T_target']} K and {results[i]['T_target']} K")
        print(f"  (RDF peak dropped from {rdf_peaks[i-1]:.1f} to {rdf_peaks[i]:.1f})")
        break

total_steps = len(temperatures) * (equil_steps + prod_steps)
total_time = sum(r["time_s"] for r in results)
print(f"\nTotal: {total_steps} MD steps in {total_time:.0f}s ({total_time/total_steps*1000:.1f} ms/step)")
print(f"Throughput: {total_steps * len(atoms) / total_time:.0f} atom-steps/s")

print("\n=== Cu Melting Simulation COMPLETE ===")
