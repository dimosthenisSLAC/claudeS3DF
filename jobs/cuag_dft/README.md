# Cu-Ag DFT Calculations for ISAAC Transfer Test

## Purpose
Compute CO adsorption energies on Cu-Ag alloy surfaces to support
the Autocatalysis microkinetic model's blind prediction of Cu-Ag
selectivity. CatHub has pure metals (Cu, Ag) but not alloys.

## Calculations (5 systems)

| System | Atoms | Purpose |
|---|---|---|
| Cu3Ag(111) + CO | 18 | Alloy binding: does Ag dilute Cu's CO affinity? |
| CuAg(111) + CO | 18 | 50:50 alloy — matches experimental composition |
| CuAg3(111) + CO | 18 | Ag-rich: CO binding on Cu sites surrounded by Ag |
| Cu\|Ag interface + CO | 34 | Binding gradient across the Cu-Ag boundary |
| Ag(111) + 2CO | 40 | Coverage-dependent binding on Ag |

## How to run

```bash
# On S3DF (iana node):

# 1. Find VASP and pseudopotentials
module avail vasp
# Set VASP_PP_PATH to wherever PBE pseudopotentials are

# 2. For each system, set up and submit:
for sys in Cu3Ag_111 CuAg_111 CuAg3_111 Cu_Ag_interface Ag_111_2CO; do
    cd jobs/cuag_dft/$sys
    cp ../INCAR .
    cp ../KPOINTS .
    # Generate POTCAR from POSCAR elements (need VASP_PP_PATH set)
    # For Cu_Ag systems: cat $VASP_PP_PATH/Cu/POTCAR $VASP_PP_PATH/Ag/POTCAR > POTCAR
    # For Ag_2CO: cat $VASP_PP_PATH/Ag/POTCAR $VASP_PP_PATH/C/POTCAR $VASP_PP_PATH/O/POTCAR > POTCAR
    sbatch ../submit_vasp.sh
    cd ../../..
done
```

## After completion

Extract E_ads = E(slab+CO) - E(slab_clean) for each system.
Clean slab calculations needed too (same POSCAR without CO).

Results feed back to: `~/Dropbox/dev/Autocatalysis/autocatlab_integration.py`

## INCAR notes
- GGA = RP (RPBE functional) — matches CatHub reference data
- ISPIN = 1 — Cu and Ag are non-magnetic
- ENCUT = 450 eV — standard for CO adsorption
- EDIFFG = -0.03 eV/Å — forces converged to 30 meV/Å
