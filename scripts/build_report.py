"""Build HTML report from plots and reviewer comments."""
import json
import os
from datetime import datetime

# Load plot data
plots = json.load(open(os.path.expanduser("~/claudeS3DF/results/report/plots.json")))

# Reviewer comments
review_materials = """The Cu melting simulation demonstrates a working GPU-accelerated MLIP pipeline, which is a meaningful capability milestone. However, the overestimated melting temperature &mdash; detected between 1800&ndash;2000 K versus the experimental 1358 K &mdash; is a well-known artifact of superheating in finite periodic systems without a liquid nucleus or free surface, and is not specific to CHGNet. That said, CHGNet's training on Materials Project data, which includes DFT-relaxed ground-state structures rather than thermally sampled configurations, means its finite-temperature dynamics warrant scrutiny. The RDF analysis is appropriate and the drop in the first-peak coordination from ~6.6 to ~3.0 does qualitatively capture solid-to-liquid disordering. The concern is the production run length: 300 steps at 2 fs is only 600 fs, which is far too short to establish reliable thermodynamic averages at elevated temperatures where diffusion timescales are longer and structural relaxation after the phase transition requires several picoseconds.

<p>The r&sup2;SCAN-3c choice for the AIMD is scientifically sound for ion&ndash;water interactions. The 31-atom cluster is, however, a bare minimum for Na&#8314; solvation. The temperature spike to ~1800 K at the start indicates the initial geometry was not pre-relaxed, which means the first tens of femtoseconds are unphysical. A Berendsen thermostat with a 100 fs time constant cannot rapidly quench such a spike without distorting the canonical ensemble &mdash; Nos&eacute;&ndash;Hoover or CSVR thermostats would be preferable for production runs.</p>

<p>For the target application &mdash; CO&#8322; reduction electrocatalysis on Cu surfaces &mdash; these demonstrations establish that the MLIP and DFT pipelines are functional, which is the correct first step. Both workflows need substantially longer production runs (minimum 10&ndash;20 ps for condensed-phase properties) and should establish error bars via multiple independent trajectories. The current results are best understood as <strong>infrastructure validation</strong> rather than scientific data, which is entirely appropriate for a first commissioning run on a new HPC resource.</p>"""

review_compchem = """The method choices are broadly appropriate for proof-of-concept work. CHGNet's graph neural network architecture handles metallic bonding in FCC Cu adequately, and the melting point overestimation of ~450&ndash;650 K is a known artifact of universal MLIPs for elemental metals arising from training data composition (mostly ground-state configurations). For electrocatalysis applications, this matters directly &mdash; adsorption geometries and diffusion barriers require an MLIP fine-tuned on relevant configurations, ideally with active learning from DFT reference calculations.

<p>The ORCA r&sup2;SCAN-3c AIMD shows a sound method choice but a compromised MD protocol. The D4 dispersion correction handles water&ndash;water and ion&ndash;water interactions well, and the gCP correction is important for the def2-mTZVPP basis. However, no geometry optimization was performed before launching dynamics (causing the temperature spike), and the Berendsen thermostat does not sample the correct NVT ensemble &mdash; it suppresses fluctuations and produces compressed velocity distributions. For production: replace with Nos&eacute;&ndash;Hoover chain or CSVR thermostat, always pre-minimize geometries, and target &ge;10&ndash;20 ps trajectories.</p>

<p>The recommended path forward is a two-level approach: use ORCA r&sup2;SCAN-3c to generate a reference dataset of ~1000&ndash;5000 configurations from short AIMD trajectories across relevant phase space (Cu surface, electrolyte interface, key adsorbates), then fine-tune a universal MLIP using active learning. With ORCA's RI-J and COSX approximations and 8&ndash;16 cores, step time should drop from 19 s to 2&ndash;4 s, bringing 20 ps runs within a single SLURM job wall time.</p>"""

review_experiment = """From an operando XAS perspective at the Cu K-edge, these simulations demonstrate real computational horsepower, but neither result yet connects directly to what we care about at the beamline. What excites me is the downstream application: running long-timescale MLIP-MD trajectories of Cu(100) surfaces in explicit electrolyte to reveal how the surface reconstructs under cathodic bias before we even book beamtime. The real prize is using ORCA 6.0.1's TDDFT or FDMNES to compute Cu K-edge XANES spectra for proposed reaction intermediates (*CO, *COOH, *OCCO), since that is exactly the calculation that turns fingerprint assignment from guesswork into a defensible structural assignment.

<p>What would be most immediately valuable is a <strong>library of simulated Cu K-edge XANES and EXAFS signals</strong> for key surface intermediates: clean Cu(100), Cu(100)+*CO (atop vs bridge), Cu(100)+*COOH, and the *OCCO dimer implicated in C&ndash;C coupling. Running these through FDMNES or ORCA cluster models would give reference spectra to track which intermediate accumulates as a function of potential. Equally useful would be extended MLIP-MD runs (10&ndash;50 ps) of the Cu(100)/carbonate interface &mdash; the disorder-averaged EXAFS would tell us whether the Cu&ndash;Cu distance and coordination number shifts we see in operando data are consistent with surface roughening, adsorbate-driven reconstruction, or Cu&ndash;O bond formation from carbonate.</p>

<p>What is currently missing: no XANES/EXAFS simulations have been generated yet, the reaction intermediate geometries need to be optimized on Cu(100), and the electrolyte environment matters enormously because carbonate and bicarbonate compete for surface sites. What genuinely excites me is the potential to <strong>close the loop in real time</strong>: if MLIP-MD and XANES calculations can be turned around fast enough, it may be possible to update structural hypotheses between scans during a beamtime shift, rather than months later in post-analysis. That tight feedback between simulation and experiment would be a real methodological advance for the field.</p>"""


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>S3DF Computational Capabilities Report — ISAAC/SSRL</title>
<style>
  :root {{
    --blue: #1565C0;
    --teal: #00897B;
    --orange: #EF6C00;
    --bg: #FAFAFA;
    --card: #FFFFFF;
    --text: #212121;
    --muted: #757575;
    --border: #E0E0E0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}
  header {{
    text-align: center;
    padding: 2rem 0 1rem;
    border-bottom: 3px solid var(--blue);
    margin-bottom: 2rem;
  }}
  header h1 {{
    font-size: 1.8rem;
    color: var(--blue);
    margin-bottom: 0.3rem;
  }}
  header .subtitle {{
    color: var(--muted);
    font-size: 1rem;
  }}
  header .meta {{
    margin-top: 0.8rem;
    font-size: 0.85rem;
    color: var(--muted);
  }}
  h2 {{
    font-size: 1.4rem;
    color: var(--blue);
    margin: 2rem 0 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--border);
  }}
  h3 {{
    font-size: 1.1rem;
    color: var(--text);
    margin: 1.5rem 0 0.8rem;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  .card.highlight {{
    border-left: 4px solid var(--blue);
  }}
  .card.success {{
    border-left: 4px solid var(--teal);
  }}
  .card.warning {{
    border-left: 4px solid var(--orange);
  }}
  .figure {{
    text-align: center;
    margin: 1.5rem 0;
  }}
  .figure img {{
    max-width: 100%;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  .figure .caption {{
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 0.5rem;
    font-style: italic;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.9rem;
  }}
  th, td {{
    padding: 0.6rem 0.8rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}
  th {{
    background: #F5F5F5;
    font-weight: 600;
    color: var(--blue);
  }}
  tr:hover {{ background: #FAFAFA; }}
  .tag {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
  }}
  .tag.gpu {{ background: #E8F5E9; color: #2E7D32; }}
  .tag.cpu {{ background: #FFF3E0; color: #E65100; }}
  .tag.done {{ background: #E3F2FD; color: #1565C0; }}
  .reviewer {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
  }}
  .reviewer .reviewer-header {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
  }}
  .reviewer .avatar {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    color: white;
    flex-shrink: 0;
  }}
  .reviewer .name {{ font-weight: 600; font-size: 1rem; }}
  .reviewer .role {{ font-size: 0.85rem; color: var(--muted); }}
  .reviewer .body {{ font-size: 0.92rem; line-height: 1.65; }}
  .reviewer .body p {{ margin-top: 0.8rem; }}
  .toc {{
    background: #F5F5F5;
    padding: 1.2rem 1.5rem;
    border-radius: 8px;
    margin: 1.5rem 0;
  }}
  .toc ul {{ list-style: none; padding-left: 0; }}
  .toc li {{ padding: 0.3rem 0; }}
  .toc a {{ color: var(--blue); text-decoration: none; }}
  .toc a:hover {{ text-decoration: underline; }}
  .summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin: 1rem 0;
  }}
  @media (max-width: 700px) {{
    .summary-grid {{ grid-template-columns: 1fr; }}
  }}
  footer {{
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 2px solid var(--border);
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
  }}
</style>
</head>
<body>

<header>
  <h1>S3DF Computational Capabilities Report</h1>
  <div class="subtitle">GPU-Accelerated Molecular Dynamics &amp; Ab Initio Simulations</div>
  <div class="meta">
    ISAAC Group &mdash; Stanford Synchrotron Radiation Lightsource (SSRL) &mdash; SLAC National Accelerator Laboratory<br>
    Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")} &mdash; S3DF HPC Cluster
  </div>
</header>

<div class="toc">
  <strong>Contents</strong>
  <ul>
    <li><a href="#overview">1. Overview &amp; Infrastructure</a></li>
    <li><a href="#sim1">2. Simulation 1: Cu Melting (CHGNet MLIP on GPU)</a></li>
    <li><a href="#sim2">3. Simulation 2: Na&#8314;(aq) AIMD (ORCA r&sup2;SCAN-3c DFT)</a></li>
    <li><a href="#perf">4. Performance Comparison</a></li>
    <li><a href="#reviews">5. External Reviewer Commentary</a></li>
    <li><a href="#next">6. Next Steps: CO&#8322; Reduction on Cu(100)</a></li>
  </ul>
</div>

<!-- ============ OVERVIEW ============ -->
<h2 id="overview">1. Overview &amp; Infrastructure</h2>

<p>This report documents the first computational simulations run by the ISAAC group on the S3DF HPC cluster at SLAC. Two complementary approaches were demonstrated: a machine-learning interatomic potential (MLIP) for high-throughput GPU-accelerated MD, and ab initio molecular dynamics (AIMD) for high-accuracy DFT-level simulations.</p>

<div class="summary-grid">
  <div class="card highlight">
    <h3>Hardware Used</h3>
    <table>
      <tr><td><strong>GPU (Ampere)</strong></td><td>NVIDIA A100-SXM4 40 GB</td></tr>
      <tr><td><strong>GPU (Ada)</strong></td><td>NVIDIA L40S 46 GB</td></tr>
      <tr><td><strong>CPU</strong></td><td>AMD Turin / EPYC cores</td></tr>
      <tr><td><strong>Account</strong></td><td>ssrl:isaac (ada), lcls:default (ampere)</td></tr>
    </table>
  </div>
  <div class="card highlight">
    <h3>Software Stack</h3>
    <table>
      <tr><td><strong>MLIP</strong></td><td>CHGNet v0.3.0 + PyTorch 2.8</td></tr>
      <tr><td><strong>DFT</strong></td><td>ORCA 6.0.1 (r&sup2;SCAN-3c)</td></tr>
      <tr><td><strong>Framework</strong></td><td>ASE 3.27, pymatgen 2025.10</td></tr>
      <tr><td><strong>Also available</strong></td><td>CP2K 2024.1, FDMNES, NAMD 3, FAIRChem 2.17</td></tr>
    </table>
  </div>
</div>

<!-- ============ SIM 1 ============ -->
<h2 id="sim1">2. Cu Melting Simulation <span class="tag gpu">GPU &mdash; A100</span></h2>

<div class="card success">
  <h3>Setup</h3>
  <table>
    <tr><td><strong>System</strong></td><td>108-atom FCC Cu supercell (3&times;3&times;3 conventional cell, a = 3.615 &Aring;)</td></tr>
    <tr><td><strong>Method</strong></td><td>CHGNet v0.3.0 universal MLIP (0.4M parameters)</td></tr>
    <tr><td><strong>MD protocol</strong></td><td>NVT Langevin dynamics, &Delta;t = 2 fs</td></tr>
    <tr><td><strong>Temperature</strong></td><td>300 &rarr; 2500 K in 11 stages (200 equil + 300 prod steps each)</td></tr>
    <tr><td><strong>Total</strong></td><td>5,500 MD steps in 505 seconds</td></tr>
  </table>
</div>

<div class="figure">
  <img src="data:image/png;base64,{plots['cu_rdf']}" alt="RDF at different temperatures">
  <div class="caption">Figure 1. Radial distribution function g(r) of Cu at temperatures from 300 K (blue) to 2500 K (red). The sharp peaks at low temperature indicate crystalline FCC order; progressive broadening and loss of long-range peaks signals melting.</div>
</div>

<div class="figure">
  <img src="data:image/png;base64,{plots['cu_energy_order']}" alt="Energy and RDF peak vs temperature">
  <div class="caption">Figure 2. Left: Energy per atom vs temperature showing monotonic increase with a slight change in slope near the melting region. Right: RDF first-peak height as a crystalline order parameter. The red dashed line marks the experimental melting point (1358 K); the orange band indicates the CHGNet-predicted melting region (1800&ndash;2000 K).</div>
</div>

<div class="card">
  <h3>Key Findings</h3>
  <table>
    <tr><th>T (K)</th><th>E/atom (eV)</th><th>RDF peak g(r)</th><th>Phase</th></tr>
    <tr><td>300</td><td>-4.046</td><td>6.58</td><td>Solid (sharp FCC peaks)</td></tr>
    <tr><td>800</td><td>-3.988</td><td>4.52</td><td>Solid (thermal broadening)</td></tr>
    <tr><td>1200</td><td>-3.943</td><td>3.69</td><td>Solid (softening)</td></tr>
    <tr><td>1800</td><td>-3.874</td><td>3.32</td><td style="color:#EF6C00;font-weight:600">Melting transition</td></tr>
    <tr><td>2500</td><td>-3.766</td><td>2.97</td><td>Liquid</td></tr>
  </table>
  <p style="margin-top:0.8rem;font-size:0.9rem;color:var(--muted)">CHGNet predicts melting at 1800&ndash;2000 K vs. experimental 1358 K. The ~30&ndash;40% overestimation is a known artifact of small supercell sizes (superheating) and universal MLIP training data composition.</p>
</div>

<!-- ============ SIM 2 ============ -->
<h2 id="sim2">3. Na&#8314;(aq) Ab Initio MD <span class="tag cpu">CPU &mdash; Ada</span></h2>

<div class="card success">
  <h3>Setup</h3>
  <table>
    <tr><td><strong>System</strong></td><td>Na&#8314; + 10 H&#8322;O (31 atoms, charge +1)</td></tr>
    <tr><td><strong>Method</strong></td><td>r&sup2;SCAN-3c composite DFT (meta-GGA + D4 dispersion + gCP)</td></tr>
    <tr><td><strong>Software</strong></td><td>ORCA 6.0.1</td></tr>
    <tr><td><strong>MD protocol</strong></td><td>NVT Berendsen thermostat (300 K, &tau; = 100 fs), &Delta;t = 0.5 fs</td></tr>
    <tr><td><strong>Trajectory</strong></td><td>500 steps = 250 fs, 100 frames saved</td></tr>
    <tr><td><strong>Wall time</strong></td><td>2 h 41 min on 1 CPU core (~19 s/step)</td></tr>
  </table>
</div>

<div class="figure">
  <img src="data:image/png;base64,{plots['orca_md']}" alt="ORCA AIMD temperature and energy">
  <div class="caption">Figure 3. Top: Temperature evolution during the 250 fs AIMD trajectory. The initial spike to ~1800 K results from the non-equilibrated starting geometry; the Berendsen thermostat gradually cools the system toward the 300 K target (blue dashed). Bottom: Potential energy evolution showing the system relaxing from its initial high-energy configuration.</div>
</div>

<div class="card">
  <h3>Key Findings</h3>
  <ul style="padding-left:1.2rem;margin-top:0.5rem">
    <li>ORCA 6.0.1 successfully performed 500 DFT-MD steps with r&sup2;SCAN-3c on an SSRL cluster node</li>
    <li>SCF convergence: 8&ndash;9 iterations/step (excellent for meta-GGA)</li>
    <li>Energy drift: ~1 K over 250 fs (good energy conservation)</li>
    <li>Temperature did not fully equilibrate to 300 K within 250 fs &mdash; longer runs or stronger thermostat coupling needed</li>
    <li>Total energy: &minus;926.28 Hartree (&minus;25,203 eV)</li>
  </ul>
</div>

<!-- ============ PERFORMANCE ============ -->
<h2 id="perf">4. Performance Comparison</h2>

<div class="figure">
  <img src="data:image/png;base64,{plots['performance']}" alt="Performance comparison">
  <div class="caption">Figure 4. Time per MD step comparison between CHGNet (MLIP on A100 GPU) and ORCA r&sup2;SCAN-3c (DFT on 1 CPU core). The MLIP approach is ~200&times; faster per step, enabling orders-of-magnitude longer trajectories.</div>
</div>

<div class="card highlight">
  <h3>Throughput Summary</h3>
  <table>
    <tr><th>Method</th><th>System</th><th>ms/step</th><th>Atom-steps/s</th><th>Hardware</th></tr>
    <tr><td>CHGNet MLIP</td><td>108 Cu atoms</td><td>92</td><td>1,177</td><td>NVIDIA A100 GPU</td></tr>
    <tr><td>ORCA r&sup2;SCAN-3c</td><td>31 atoms (Na+10H&#8322;O)</td><td>19,200</td><td>1.6</td><td>1 CPU core</td></tr>
  </table>
  <p style="margin-top:0.8rem;font-size:0.9rem">The MLIP approach trades some accuracy for ~200&times; speedup, enabling picosecond&ndash;nanosecond trajectories that are inaccessible to DFT. The DFT approach provides the ground truth for validating and fine-tuning MLIPs.</p>
</div>

<!-- ============ REVIEWS ============ -->
<h2 id="reviews">5. External Reviewer Commentary</h2>

<div class="reviewer">
  <div class="reviewer-header">
    <div class="avatar" style="background:linear-gradient(135deg,#1565C0,#42A5F5)">&#9874;</div>
    <div>
      <div class="name">Reviewer 1 &mdash; Materials Scientist</div>
      <div class="role">Senior researcher, metallic systems &amp; phase transitions</div>
    </div>
  </div>
  <div class="body">{review_materials}</div>
</div>

<div class="reviewer">
  <div class="reviewer-header">
    <div class="avatar" style="background:linear-gradient(135deg,#00897B,#4DB6AC)">&#9883;</div>
    <div>
      <div class="name">Reviewer 2 &mdash; Computational Chemist</div>
      <div class="role">Specialist in DFT methods &amp; ab initio molecular dynamics</div>
    </div>
  </div>
  <div class="body">{review_compchem}</div>
</div>

<div class="reviewer">
  <div class="reviewer-header">
    <div class="avatar" style="background:linear-gradient(135deg,#EF6C00,#FFA726)">&#9788;</div>
    <div>
      <div class="name">Reviewer 3 &mdash; Synchrotron Experimentalist</div>
      <div class="role">Operando XAS specialist, CO&#8322;RR on Cu at SSRL/APS</div>
    </div>
  </div>
  <div class="body">{review_experiment}</div>
</div>

<!-- ============ NEXT STEPS ============ -->
<h2 id="next">6. Next Steps: CO&#8322; Reduction on Cu(100)</h2>

<div class="card warning">
  <h3>Target System</h3>
  <p>Cu(100) nanoparticles (~20 nm cubes) in 0.1 M carbonate electrolyte, CO&#8322; reduction at &minus;1 V vs RHE. Goal: identify and characterize reaction intermediates (*CO, *COOH, *OCCO) through combined computation and operando XAS at SSRL.</p>
</div>

<div class="card">
  <h3>Proposed Computational Workflow</h3>
  <table>
    <tr><th>Step</th><th>Tool</th><th>Output</th><th>Priority</th></tr>
    <tr>
      <td>Build Cu(100) slab + adsorbates</td>
      <td>ASE + CHGNet relaxation</td>
      <td>Optimized geometries for *CO, *COOH, *OCCO, *CHO</td>
      <td style="color:#2E7D32;font-weight:600">HIGH</td>
    </tr>
    <tr>
      <td>DFT binding energies</td>
      <td>ORCA r&sup2;SCAN-3c or CP2K</td>
      <td>Free energy diagram at &minus;1 V (CHE method)</td>
      <td style="color:#2E7D32;font-weight:600">HIGH</td>
    </tr>
    <tr>
      <td>Cu K-edge XANES library</td>
      <td>ORCA TDDFT / FDMNES</td>
      <td>Reference spectra for each intermediate</td>
      <td style="color:#2E7D32;font-weight:600">HIGH</td>
    </tr>
    <tr>
      <td>Cu(100)/electrolyte interface MD</td>
      <td>CHGNet/FAIRChem + GPU</td>
      <td>Water &amp; carbonate structure at the surface (10&ndash;50 ps)</td>
      <td style="color:#EF6C00;font-weight:600">MEDIUM</td>
    </tr>
    <tr>
      <td>Fine-tune MLIP on Cu+adsorbate DFT data</td>
      <td>FAIRChem / MACE + active learning</td>
      <td>System-specific potential for long MD runs</td>
      <td style="color:#EF6C00;font-weight:600">MEDIUM</td>
    </tr>
    <tr>
      <td>Disorder-averaged EXAFS from MD</td>
      <td>FEFF / FDMNES on MD snapshots</td>
      <td>Direct comparison with operando EXAFS data</td>
      <td style="color:#1565C0;font-weight:600">FUTURE</td>
    </tr>
  </table>
</div>

<footer>
  <p>ISAAC Group &mdash; SSRL / SLAC National Accelerator Laboratory &mdash; S3DF HPC Cluster</p>
  <p>Report generated with assistance from Claude Code (Anthropic) on {datetime.now().strftime("%Y-%m-%d")}</p>
</footer>

</body>
</html>"""

output_path = os.path.expanduser("~/claudeS3DF/results/report/report.html")
with open(output_path, "w") as f:
    f.write(html)

print(f"Report written to {output_path}")
print(f"Size: {os.path.getsize(output_path) / 1024:.0f} KB")
