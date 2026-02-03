# Artifact for HPDC 2026 Submission  
**Anonymous Submission — Digital-Twin Simulation of Hybrid Quantum–Classical Cloud Systems**

---

## Overview

This repository contains the artifact associated with an HPDC 2026 submission describing a digital-twin simulation framework for hybrid quantum–classical cloud environments.

The artifact reproduces the core experimental results presented in the paper, including:

- Hybrid QPU–CPU workflow execution modeling  
- Resource allocation and contention modeling  
- Energy and power analysis across heterogeneous devices  
- Iteration-driven workload scaling behavior  

Two primary experiments are included:

1. `main.ipynb` — Baseline hybrid cloud simulation and energy evaluation  
2. `Experiment-job-iters.ipynb` — Iteration-scaling experiment analyzing performance and energy trends  

The framework models orchestration-level behavior (not physical quantum simulation) and captures:

- Job arrivals  
- Workflow iterations  
- Multi-device resource allocation  
- Blocking and queuing  
- Power and energy consumption  
- Cost modeling  

---

## System Requirements

- Python ≥ 3.10  
- Recommended: Conda or virtual environment  
- OS: Linux or macOS (tested), Windows should also work  

---

## Installation

Clone the repository:

```bash
git clone <artifact-repository-url>
cd <repository>
```
Create and activate a virtual environment (recommended):
```
python -m venv venv
source venv/bin/activate
```
Install dependencies:
```
pip install -r requirements.txt
```

⸻

Running the Experiments

Experiment 1: Baseline Hybrid Simulation

Open ```main.ipynb``` and execute all cells sequentially.

Expected outputs:
- Power time-series plots
- Energy summaries
- Per-job energy distributions
- Cost estimates (if enabled)

⸻

Experiment 2: Iteration Scaling Study

Notebook:
```
Experiment-job-iters.ipynb
```
This experiment evaluates the impact of increasing workflow iteration counts on:
- Total simulation time
- QPU energy consumption
- CPU energy consumption
- Variability across runs

The iteration set evaluated in the paper is:

{3, 6, 9, 12, 15, 18, 21}

Outputs include:
- Iterations vs total simulation time
- Dual-axis QPU/CPU energy plots
- Variability analysis plots
- Summary statistics tables

Execute all cells sequentially to reproduce the results.

⸻

Reproducibility Notes
- Random workload generation uses fixed seeds where specified in the notebooks.
- Simulation results are deterministic given identical configuration and seed.
- Runtime depends on workload size; typical execution time on a modern laptop is several minutes.

⸻

Artifact Structure
```
.
├── main.ipynb
├── Experiment-job-iters.ipynb
├── requirements.txt
├── data/
├── figures/
└── src/
```
- src/ contains simulation core components.
- data/ stores generated workloads (if persisted).
- figures/ contains exported plots.

⸻

Configuration

Key parameters that can be modified inside the notebooks:
- Number of QPUs
- Number of CPUs
- QPU baseline power (W)
- CPU idle/peak power (W)
- Workload size
- Iteration counts

Adjusting these parameters enables sensitivity analysis beyond the paper.

⸻

Expected Hardware Resources

The artifact is lightweight and does not require access to real quantum hardware.

Typical resource usage:
- RAM: < 4 GB
- CPU: 2–8 cores recommended

⸻

Notes for Artifact Evaluation Committee
- All experiments are self-contained.
- No external APIs or cloud access are required.
- No proprietary datasets are used.
- All plots are generated directly within the notebooks.

If any issue arises during execution, please ensure:
- Python version ≥ 3.10
- All dependencies are installed
- Notebook cells are executed in order

⸻

License

Released for academic artifact evaluation purposes.

