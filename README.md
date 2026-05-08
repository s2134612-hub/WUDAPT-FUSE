# WUDAPT-FUSE

**A workstation-runnable analytical framework for testing whether building morphology, topology, or geographic position governs within-class urban heat exposure inequality at the 100-m scale.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20080489.svg)](https://doi.org/10.5281/zenodo.20080489)
[![GitHub release](https://img.shields.io/github/v/release/s2134612-hub/WUDAPT-FUSE)](https://github.com/s2134612-hub/WUDAPT-FUSE/releases)

---

## Overview

WUDAPT-FUSE fuses four open data sources (ERA5-HEAT, the Demuzere global Local Climate Zone map, WorldPop 2020 gridded population, and OpenStreetMap building footprints) into a single 100-m grid and synthesises hourly Universal Thermal Climate Index (UTCI) fields using a deviation-injection method. It then applies a population-weighted Pyatt–Yitzhaki Gini decomposition to test four competing hypotheses about within-class urban heat inequality:

- **H1 — Morphology** (8 OSM-derived urban morphological parameters)
- **H2 — Topology** (5 persistent-homology proxies of the heat field)
- **H3 — Hybrid** (form + topology, 13 features)
- **H4 — Geographic position** (coast distance, mountain distance, elevation proxy)

Applied to three Greater Bay Area (GBA) cities — Shenzhen, Guangzhou, Dongguan — across four seasons of 2020, the framework produces 12 figures, 10 tables, and a complete cross-city validation in **under 5 minutes** on a single GPU workstation.

### Key result

> Within-class heat inequality is governed by **geographic position** (coast / mountain distance), not by building form or local topology. Morphology absorbs only **1.0 percentage point** of the within-class Gini share; geography absorbs **10.8 pp**.

---

## Companion paper

This repository accompanies:

> Luo, Y. (2026). *Geographic position, not building morphology, governs within-class urban heat inequality: a population-weighted Gini decomposition framework (WUDAPT-FUSE) for the Greater Bay Area.* Submitted to *Sustainable Cities and Society*.

---

## Repository structure

```
WUDAPT-FUSE/
├── README.md                              # this file
├── LICENSE                                # MIT licence
├── requirements.txt                       # Python dependencies
├── environment.yml                        # Conda environment spec
├── .gitignore
│
├── src/                                   # core library code
│   └── utils/
│       ├── config.py                      # paths, bbox, study period
│       ├── cities.py                      # Shenzhen / Guangzhou / Dongguan configs
│       ├── figure_style.py                # Nature/SCS-compliant matplotlib style
│       └── logging.py                     # structured logger
│
├── scripts/                               # end-to-end pipeline scripts (numbered phases)
│   ├── download_era5_heat.py              # Phase 1: ERA5-HEAT UTCI from CDS
│   ├── download_lcz.py                    # Phase 1: Demuzere global LCZ map
│   ├── download_osm_buildings.py          # Phase 1: OSM footprints via OSMnx
│   ├── align_grids.py                     # Phase 1: reproject all sources to 100-m UTM
│   ├── compute_umps.py                    # Phase 2: 8 urban morphological parameters
│   ├── full_pipeline_july.py              # Phase 2-3: 100-m UTCI synthesis (deviation-injection)
│   ├── utci_inequality.py                 # Phase 2: Gini + Lorenz, generates Fig 3
│   ├── lcz_subcategories.py               # Phase 3: k-means + Silhouette, generates Fig 4
│   ├── subcategory_inequality.py          # Phase 3: subcategory Gini, generates Fig 5 (key)
│   ├── tda_analysis.py                    # Phase 4: TDA via GUDHI, generates Fig 6
│   ├── hybrid_subcategorization.py        # Phase 5: hybrid form+topology, Fig 7
│   ├── phase6_nonspatial.py               # Phase 6: 6-scheme comparison, Fig 8 (breakthrough)
│   ├── phase6_5_physical_mechanism.py     # Phase 6.5: coast/mountain decomposition, Fig 9
│   ├── phase7_diurnal_validation.py       # Phase 7-L1: diurnal split, Fig 10
│   ├── phase7_seasonal_validation.py      # Phase 7-L2: 4 seasons, Fig 11
│   ├── multicity_analysis.py              # Phase 8: cross-city transfer, Fig 12
│   │
│   ├── make_fig01_concept.py              # Fig 1: study site & input data
│   ├── make_framework_standalone.py       # Fig 2: WUDAPT-FUSE framework
│   ├── batch_export_vectors.py            # bulk PNG → SVG/PDF export
│   │
│   ├── build_paper_with_figures.py        # pandoc + figure embedding
│   └── apply_scs_formatting.py            # SCS submission formatting (TNR 12pt, 2.0 line spacing,
│                                          # 2.5 cm margins, line numbers, page numbers)
│
├── configs/                               # YAML configuration files
├── data/                                  # local data (gitignored — see Data Availability)
│   ├── raw/                               # downloaded source rasters
│   └── processed/                         # aligned 100-m grids
├── results/                               # CSV outputs of each phase (kept in repo)
├── figures/                               # 12 figures × 3 formats (PNG/SVG/PDF)
└── docs/
    └── paper/
        ├── PAPER_FULL.md                  # source markdown
        └── WUDAPT-FUSE_SCS_submission_*.docx
```

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/s2134612-hub/WUDAPT-FUSE.git
cd WUDAPT-FUSE
conda env create -f environment.yml
conda activate wudapt
```

Or with pip:

```bash
pip install -r requirements.txt
```

### 2. Configure data sources (one-time)

Set up your **Copernicus Climate Data Store API key** at `~/.cdsapirc` (free registration at https://cds.climate.copernicus.eu).

### 3. Run the full pipeline (≈ 5 min on a GPU workstation)

```bash
python scripts/full_pipeline_july.py        # synthesize 100-m UTCI for July 2020
python scripts/utci_inequality.py           # Phase 2 — generates Fig 3
python scripts/lcz_subcategories.py         # Phase 3 — generates Fig 4
python scripts/subcategory_inequality.py    # Phase 3 — generates Fig 5 (key result)
python scripts/tda_analysis.py              # Phase 4 — generates Fig 6
python scripts/hybrid_subcategorization.py  # Phase 5 — generates Fig 7
python scripts/phase6_nonspatial.py         # Phase 6 — generates Fig 8 (breakthrough)
python scripts/phase6_5_physical_mechanism.py  # Phase 6.5 — Fig 9
python scripts/phase7_diurnal_validation.py    # Phase 7-L1 — Fig 10
python scripts/phase7_seasonal_validation.py   # Phase 7-L2 — Fig 11
python scripts/multicity_analysis.py           # Phase 8 — Fig 12
```

### 4. Reproduce paper figures and tables

All 12 figures are produced under `figures/` in three formats (PNG for display, SVG for editing, PDF for submission). All 10 tables are written as CSV under `results/`.

### 5. Compile the manuscript

```bash
python scripts/build_paper_with_figures.py    # markdown → docx with embedded figures
python scripts/apply_scs_formatting.py        # apply SCS submission formatting
```

---

## Data sources

| Source | Resolution | Provider | Access |
|---|---|---|---|
| ERA5-HEAT (UTCI) | 25 km × 1 h | Copernicus CDS | https://cds.climate.copernicus.eu (`derived-utci-historical` v1.1) |
| LCZ map | 100 m global | Demuzere et al. (2022) | https://doi.org/10.5281/zenodo.6364594 |
| Population | 100 m gridded | WorldPop 2020 (constrained) | https://www.worldpop.org |
| Building footprints | vector polygons | OpenStreetMap | extracted via [OSMnx](https://github.com/gboeing/osmnx) |

---

## Reproducibility statement

- All code is version-controlled in this repository (MIT licence).
- Derived 100-m hourly UTCI fields, LCZ subcategory grids, urban morphological parameters, and Gini decomposition results for the three GBA cities are archived at Zenodo (DOI: pending).
- The full pipeline runs end-to-end in **under 5 minutes** on a single workstation (NVIDIA RTX 3060 12 GB, 16 cores, 16 GB RAM, Windows 11).
- Random seeds are fixed for k-means clustering (`random_state=42` in scikit-learn calls).

---

## System requirements

- Python ≥ 3.10 (tested on 3.11)
- 16 GB RAM (32 GB recommended for cross-city analysis)
- ~50 GB disk space for raw data + derived products
- Optional: CUDA-capable GPU (used by PyTorch in robustness checks)

Tested on Windows 11 + miniconda; should work on Linux/macOS with the conda environment.

---

## Citation

If you use this framework, please cite **both** the paper and the software:

```bibtex
@article{Luo2026WUDAPT-FUSE,
  title   = {Geographic position, not building morphology, governs within-class urban heat inequality:
             a population-weighted Gini decomposition framework (WUDAPT-FUSE) for the Greater Bay Area},
  author  = {Luo, Yanhuo},
  journal = {Sustainable Cities and Society},
  year    = {2026},
  note    = {Manuscript submitted for publication}
}

@software{Luo2026WUDAPT-FUSE-software,
  title     = {WUDAPT-FUSE: A workstation-runnable framework for testing whether building morphology,
               topology, or geographic position governs within-class urban heat exposure inequality},
  author    = {Luo, Yanhuo},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.20080489},
  url       = {https://doi.org/10.5281/zenodo.20080489}
}
```

---

## Acknowledgments

This work uses publicly available data from the Copernicus Climate Change Service (ERA5-HEAT), the Demuzere et al. global LCZ map, WorldPop, and OpenStreetMap. The author is grateful to the supervisors and colleagues at the Institute for Advanced Studies, University of Malaya, for their guidance during this study.

---

## Contact

**Yanhuo Luo** — Institute for Advanced Studies, University of Malaya, Kuala Lumpur, Malaysia
✉ s2134612@siswa.um.edu.my

For questions or issues, please open a GitHub issue.

---

## Licence

[MIT Licence](LICENSE) — free for academic and commercial use with attribution.
