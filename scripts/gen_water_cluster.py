"""Generate a Na+ solvated in 10 water molecules for ORCA AIMD."""
import numpy as np
from ase import Atoms
from ase.build import molecule
from ase.io import write

rng = np.random.default_rng(42)

# Start with Na+ at origin
positions = [[0.0, 0.0, 0.0]]
symbols = ["Na"]

# Place 10 water molecules in a spherical shell around Na+
# First shell: 6 waters at ~2.4 Ang (typical Na-O distance)
# Second shell: 4 waters at ~4.0 Ang
n_first = 6
n_second = 4
r_first = 2.4
r_second = 4.2

def random_water_at(center, rng):
    """Return O, H, H positions for a water molecule centered at `center`,
    with O at center and random orientation."""
    # O-H bond length 0.96 Ang, H-O-H angle 104.5 deg
    d_oh = 0.96
    half_angle = np.radians(104.5 / 2)

    # Random rotation
    axis = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    angle = rng.uniform(0, 2 * np.pi)

    # H positions in local frame (O at origin)
    h1_local = np.array([d_oh * np.sin(half_angle), d_oh * np.cos(half_angle), 0.0])
    h2_local = np.array([-d_oh * np.sin(half_angle), d_oh * np.cos(half_angle), 0.0])

    # Simple rotation using Rodrigues' formula
    def rotate(v, k, theta):
        return (v * np.cos(theta) +
                np.cross(k, v) * np.sin(theta) +
                k * np.dot(k, v) * (1 - np.cos(theta)))

    h1 = center + rotate(h1_local, axis, angle)
    h2 = center + rotate(h2_local, axis, angle)

    return [center, h1, h2]

def distribute_on_sphere(n, radius, rng):
    """Distribute n points roughly evenly on a sphere."""
    points = []
    for i in range(n):
        # Golden spiral distribution with small random perturbation
        phi = np.arccos(1 - 2 * (i + 0.5) / n)
        theta = np.pi * (1 + 5**0.5) * i + rng.uniform(-0.1, 0.1)
        x = radius * np.sin(phi) * np.cos(theta)
        y = radius * np.sin(phi) * np.sin(theta)
        z = radius * np.cos(phi)
        points.append([x, y, z])
    return points

# First solvation shell
centers_1 = distribute_on_sphere(n_first, r_first, rng)
for c in centers_1:
    c = np.array(c)
    wat = random_water_at(c, rng)
    symbols.extend(["O", "H", "H"])
    positions.extend(wat)

# Second solvation shell
centers_2 = distribute_on_sphere(n_second, r_second, rng)
for c in centers_2:
    c = np.array(c)
    wat = random_water_at(c, rng)
    symbols.extend(["O", "H", "H"])
    positions.extend(wat)

atoms = Atoms(symbols=symbols, positions=positions)

# Write XYZ file
write("/sdf/home/d/dsokaras/claudeS3DF/jobs/na_water10.xyz", atoms)
print(f"Generated {len(atoms)} atoms: {atoms.get_chemical_formula()}")
print(f"Na+ at origin, {n_first} waters in first shell (~{r_first} Å), "
      f"{n_second} in second shell (~{r_second} Å)")

# Print for ORCA input
print("\nORCA coordinate block:")
for s, p in zip(symbols, positions):
    print(f"  {s:2s}  {p[0]:12.6f}  {p[1]:12.6f}  {p[2]:12.6f}")
