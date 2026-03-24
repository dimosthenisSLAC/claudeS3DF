# Coverage-Dependent Barrier Calculations on Cu(100)

## Why these calculations matter

The microkinetic model predicts C₂H₄ vs CH₄ selectivity using coverage-dependent barriers:
- C₂H₄ ∝ k_CC × exp(-ω_CC × θ/kBT) × θ²
- CH₄  ∝ k_CHO × exp(-ω_CHO × θ/kBT) × θ

The model was trained on Cu-Au flow cell data (θ ~ 0.01-0.3). When we extrapolate to
Cu-Ag GDE (θ ~ 0.3-0.7), the model can't differentiate C₂H₄ from CH₄ because the
ω values are unconstrained at high coverage.

These DFT calculations directly measure how CO binding and C-C coupling change
with surface coverage — the missing physics for GDE prediction.

## Calculations (10 VASP jobs)

### Part 1: CO binding vs coverage (6 jobs)
Cu(100) 3×3×4 slab with increasing CO coverage:

| System | CO count | θ (ML) | Atoms | Purpose |
|---|---|---|---|---|
| Cu100_clean | 0 | 0.00 | 36 | Reference slab energy |
| Cu100_1CO | 1 | 0.11 | 38 | Isolated CO binding |
| Cu100_2CO | 2 | 0.22 | 40 | Low coverage |
| Cu100_4CO | 4 | 0.44 | 44 | Moderate coverage |
| Cu100_6CO | 6 | 0.67 | 48 | High coverage |
| Cu100_8CO | 8 | 0.89 | 52 | Near saturation |

**Analysis**: Differential binding energy = E(n CO) - E((n-1) CO) - E(CO_gas)
The slope of this curve gives ω (lateral repulsion parameter).

### Part 2: C-C coupling intermediate (*OCCO) vs coverage (4 jobs)
Cu(100) with *OCCO (C-C coupled intermediate) plus spectator CO:

| System | Spectators | Total CO equiv | Purpose |
|---|---|---|---|
| Cu100_OCCO_0spec | 0 | 2 | Isolated OCCO energy |
| Cu100_OCCO_2spec | 2 | 4 | θ ~ 0.44 |
| Cu100_OCCO_4spec | 4 | 6 | θ ~ 0.67 |
| Cu100_OCCO_6spec | 6 | 8 | θ ~ 0.89 |

**Analysis**: How does the OCCO formation energy change with spectator coverage?
This directly measures ω_CC (coverage effect on C-C coupling barrier).

## How to run

```bash
cd ~/claudeS3DF
git pull

# For each calculation:
for sys in Cu100_clean Cu100_1CO Cu100_2CO Cu100_4CO Cu100_6CO Cu100_8CO \
           Cu100_OCCO_0spec Cu100_OCCO_2spec Cu100_OCCO_4spec Cu100_OCCO_6spec; do
    cd jobs/cuag_dft/coverage_series/$sys
    cp ../INCAR .
    cp ../KPOINTS .
    # Generate POTCAR (Cu + C + O for systems with CO, Cu only for clean)
    # Check POSCAR for element order
    sbatch ../../submit_vasp.sh
    cd ~/claudeS3DF
done
```

## Expected results

After all jobs complete, extract energies and compute:

```python
# Differential CO binding energy
E_diff(n) = E(n_CO) - E((n-1)_CO) - E_CO_gas

# OCCO formation energy vs coverage
E_OCCO(θ) = E(OCCO + n_spec) - E((n_spec+2)_CO)

# The coverage-dependent barrier parameter:
# ω ≈ -dE_diff/dθ (positive ω = repulsion increases with coverage)
```

Save results to `results/coverage_dependent_energies.json`:
```json
{
  "CO_differential_binding": {
    "theta_0.11": {"E_diff_eV": <value>},
    "theta_0.22": {"E_diff_eV": <value>},
    ...
  },
  "OCCO_formation": {
    "theta_0.22": {"E_form_eV": <value>},
    "theta_0.44": {"E_form_eV": <value>},
    ...
  }
}
```

Git push when done.
