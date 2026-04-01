#!/usr/bin/env python3
"""
VASP job wrapper using Custodian for automatic error handling and restarts.

Usage in SLURM scripts:
    python /path/to/run_vasp_custodian.py [--vasp-cmd CMD] [--max-errors N] [--wall-time SEC]

This replaces direct `mpirun ... vasp_std` calls. Custodian will:
- Detect 38+ VASP error types and auto-fix INCAR/restart
- Handle ZBRENT/CG oscillation by switching to IBRION=1
- Auto-restart from CONTCAR when NSW limit is hit
- Manage ALGO ladder on electronic convergence failures
- Write STOPCAR before walltime expires
- Clean corrupt WAVECAR/CHGCAR files
"""
import argparse
import os
import sys

from custodian.custodian import Custodian
from custodian.vasp.handlers import (
    VaspErrorHandler,
    UnconvergedErrorHandler,
    NonConvergingErrorHandler,
    FrozenJobErrorHandler,
    PotimErrorHandler,
    WalltimeHandler,
    DriftErrorHandler,
    LargeSigmaHandler,
    PositiveEnergyErrorHandler,
    StdErrHandler,
)
from custodian.vasp.jobs import VaspJob


def main():
    parser = argparse.ArgumentParser(description="Run VASP with Custodian error handling")
    parser.add_argument(
        "--vasp-cmd", type=str, default=None,
        help="VASP command (default: auto-detect from VASP_CMD env or use mpirun)"
    )
    parser.add_argument("--max-errors", type=int, default=10,
                        help="Max error corrections before giving up (default: 10)")
    parser.add_argument("--wall-time", type=int, default=None,
                        help="Wall time in seconds (auto-detected from SLURM if not set)")
    parser.add_argument("--scratch-dir", type=str, default=None,
                        help="Scratch directory for backups")
    parser.add_argument("--handlers", type=str, default="all",
                        help="Comma-separated handler list or 'all' (default: all)")
    args = parser.parse_args()

    # Determine VASP command
    if args.vasp_cmd:
        vasp_cmd = args.vasp_cmd.split()
    elif os.environ.get("VASP_CMD"):
        vasp_cmd = os.environ["VASP_CMD"].split()
    else:
        # Auto-detect: GPU build on ampere, CPU otherwise
        ntasks = int(os.environ.get("SLURM_NTASKS", "1"))
        partition = os.environ.get("SLURM_JOB_PARTITION", "")

        if partition == "ampere":
            # GPU build with HPC-X mpirun
            nvhpc = "/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1"
            hpcx = f"{nvhpc}/comm_libs/12.3/hpcx/hpcx-2.17.1"
            vasp_cmd = [
                f"{hpcx}/ompi/bin/mpirun", "--bind-to", "none",
                "-np", str(ntasks),
                "/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/bin_ampere/vasp_std"
            ]
            # Set required env vars for GPU build
            os.environ["LD_LIBRARY_PATH"] = ":".join([
                f"{nvhpc}/compilers/extras/qd/lib",
                f"{nvhpc}/cuda/12.3/targets/x86_64-linux/lib",
                f"{nvhpc}/compilers/lib",
                f"{hpcx}/ompi/lib",
                os.environ.get("LD_LIBRARY_PATH", ""),
            ])
            os.environ["OPAL_PREFIX"] = f"{hpcx}/ompi"
        elif partition == "ada":
            # ada also uses GPU build but L40S GPUs
            nvhpc = "/sdf/group/ssrl/dsokaras/sw/nvhpc/Linux_x86_64/24.1"
            hpcx = f"{nvhpc}/comm_libs/12.3/hpcx/hpcx-2.17.1"
            vasp_cmd = [
                f"{hpcx}/ompi/bin/mpirun", "--bind-to", "none",
                "-np", str(ntasks),
                "/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/bin_ampere/vasp_std"
            ]
            os.environ["LD_LIBRARY_PATH"] = ":".join([
                f"{nvhpc}/compilers/extras/qd/lib",
                f"{nvhpc}/cuda/12.3/targets/x86_64-linux/lib",
                f"{nvhpc}/compilers/lib",
                f"{hpcx}/ompi/lib",
                os.environ.get("LD_LIBRARY_PATH", ""),
            ])
            os.environ["OPAL_PREFIX"] = f"{hpcx}/ompi"
        else:
            # CPU build
            vasp_cmd = [
                "mpirun", "--mca", "btl", "self,vader",
                "--mca", "pml", "ob1",
                "-np", str(ntasks),
                "/sdf/group/ssrl/dsokaras/sw/vasp6/vasp.6.5.1/build/std/vasp"
            ]

    os.environ["OMP_NUM_THREADS"] = "1"

    print(f"VASP command: {' '.join(vasp_cmd)}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Partition: {os.environ.get('SLURM_JOB_PARTITION', 'unknown')}")

    # Determine wall time
    wall_time = args.wall_time
    if wall_time is None:
        # Try to get from SLURM
        try:
            import subprocess
            result = subprocess.run(
                ["squeue", "-j", os.environ.get("SLURM_JOB_ID", "0"),
                 "-h", "-o", "%l"],
                capture_output=True, text=True, timeout=10
            )
            time_str = result.stdout.strip()
            if time_str and "-" in time_str:
                days, hms = time_str.split("-")
                parts = hms.split(":")
                wall_time = int(days) * 86400 + int(parts[0]) * 3600 + int(parts[1]) * 60
            elif time_str:
                parts = time_str.split(":")
                if len(parts) == 3:
                    wall_time = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except Exception:
            pass

    # Set up handlers
    handlers = [
        VaspErrorHandler(output_filename="vasp.out"),
        UnconvergedErrorHandler(),
        NonConvergingErrorHandler(),
        PotimErrorHandler(),
        PositiveEnergyErrorHandler(),
        DriftErrorHandler(),
        LargeSigmaHandler(),
        StdErrHandler(),
    ]

    if wall_time:
        # Stop 5 minutes before walltime
        buffer_time = min(300, wall_time // 10)
        handlers.append(WalltimeHandler(wall_time=wall_time, buffer_time=buffer_time))
        print(f"Wall time: {wall_time}s (buffer: {buffer_time}s)")

    # Set up job
    jobs = [VaspJob(
        vasp_cmd=vasp_cmd,
        output_file="vasp.out",
        stderr_file="vasp.err",
        auto_npar=False,  # Don't mess with NPAR on GPU builds
        auto_gamma=True,
    )]

    # Run with Custodian
    c = Custodian(
        handlers=handlers,
        jobs=jobs,
        max_errors=args.max_errors,
        scratch_dir=args.scratch_dir,
        gzipped_output=False,
        checkpoint=True,
    )

    print(f"Starting Custodian with {len(handlers)} handlers, max_errors={args.max_errors}")
    c.run()
    print("Custodian run completed successfully.")


if __name__ == "__main__":
    main()
