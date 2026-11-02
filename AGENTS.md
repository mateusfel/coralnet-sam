# AGENTS.md — Developer & AI Agent Guidelines

> **Repository:** `d:\coralnet-sam`  
> **Project:** CoralSCOP ViT-B + BioCLIP 2.5 ReefNet (Automated Benthic Coral Reef Segmentation & Taxonomic Classification Dashboard)  
> **Target Ecosystem:** South Atlantic / Brazilian Benthic Coral Reefs (Abrolhos, Recife de Fora, etc.)

---

## 1. Project Purpose & Core Architecture

CoralSCOP + BioCLIP 2.5 ReefNet is an end-to-end computer vision and ecological surveying system designed to identify, segment, classify, and measure coral colonies in underwater benthic quadrat transect imagery.

The architecture is split between a cloud GPU inference server and a local web dashboard:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 LOCAL WORKSPACE (Flask + SVG)                           │
│  [d:\coralnet-sam]                                                                     │
│                                                                                        │
│  • Flask REST API Server (app.py)                                                      │
│  • Project Workspace Manager (src/project_manager.py)                                  │
│  • Optical Preprocessing & Session Pipeline (src/pipeline.py)                          │
│  • Few-Shot Cosine Similarity Memory (src/few_shot_memory.py)                          │
│  • Interactive SVG Canvas & Inspector (static/js/main.js & templates/index.html)        │
└────────────────────────────────────────────┬───────────────────────────────────────────┘
                                             │ HTTP POST / Tunnel
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              GOOGLE COLAB (Cloud GPU Tesla T4)                         │
│  [colab/sam_server_colab.ipynb]                                                        │
│                                                                                        │
│  1. CoralSCOP ViT-B (CVPR 2024): Promptable Foundation Model fine-tuned on corals      │
│  2. BioCLIP 2.5 ViT-H/14 ReefNet: Multi-scale zero-shot visual classifier (GPU)       │
│     - Macro: Entire colony bounding box                                                │
│     - Micro: 224x224 coralite patch at native 4K resolution                            │
│     - Outputs 512-dim L2-normalized feature embeddings + genus probabilities           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Responsibilities

```text
d:\coralnet-sam/
├── app.py                      # Flask backend, REST API routes, session coordination
├── run_pipeline.py             # CLI runner for headless batch testing
├── requirements.txt            # Python dependencies (local environment)
├── colab/
│   └── sam_server_colab.ipynb  # GPU server notebook (CoralSCOP ViT-B + BioCLIP 2.5)
├── images/                     # Default demo transect photos (sample suggestion set)
├── models/                     # Local fallback models / weights
├── src/
│   ├── project_manager.py      # Independent project directories, SHA-256 hashing, Explorer picker
│   ├── pipeline.py             # Optical filters, homography, session I/O, NMS, CSV export
│   ├── coral_classifier.py     # Taxonomic definitions, BioCLIP multi-scale inference, colors
│   ├── few_shot_memory.py      # Few-Shot signature vector memory & cosine reclassification
│   └── sam_client.py           # Colab HTTP client, healthcheck, base64 payload transport
├── static/
│   ├── css/style.css           # Dashboard CSS (dark theme, responsive canvas, project modal)
│   └── js/main.js              # Frontend logic (SVG rendering, pan/zoom, polygon editor, batch)
└── templates/
    └── index.html              # Dashboard SPA template (sidebar, canvas, modals, footer tables)
```

---

## 3. Strict Domain & Taxonomic Constraints

1. **Taxonomic Hierarchy (11 South Atlantic Coral Genera)**:
   The classifier is **strictly restricted** to the 11 valid Brazilian/South Atlantic scleractinian and hydrocoral genera:
   * *Montastraea*
   * *Mussismilia*
   * *Porites*
   * *Siderastrea*
   * *Agaricia*
   * *Millepora*
   * *Madracis*
   * *Meandrina*
   * *Stephanocoenia*
   * *Scolymia*
   * *Favia*
   * Negative class: `__NON_CORAL__` (*Não é Coral*) for non-coral benthos, turf algae, or PVC quadrat pipes.

2. **Project Isolation Outside the Repository**:
   User research projects **must always be created outside** the repository root directory (`d:\coralnet-sam`) to keep `git status` completely clean.
   Each external project directory follows this mandatory structure:
   ```text
   📁 [Project Root]/
   ├── 📄 coralscop_project.json
   ├── 📁 raw_images/
   ├── 📁 filtered_images/
   ├── 📁 polygons/
   └── 📁 exports/
   ```

3. **Cryptographic SHA-256 Hash Invalidation**:
   Polygon files are stored as `polygons/<stem>_<sha12>_polygons.json`.
   Before loading a saved session, the system computes the image file's SHA-256 hash. If the user replaces an image file with another file of the same name:
   * The hash mismatch is detected.
   * Old polygons are invalidated immediately to prevent spatial misalignment.
   * Status is set to `hash_mismatch` (`⚠️ Imagem alterada`).

---

## 4. Key Data Formats & Schemas

### A. `coralscop_project.json` (Project Root Descriptor)
```json
{
  "format_version": "1.0",
  "name": "Abrolhos_Sector_A_2026",
  "root_path": "C:\\Coral_Surveys\\Abrolhos_2026",
  "created_at": "2026-11-01T21:10:00Z",
  "last_opened_at": "2026-11-01T21:15:00Z",
  "dirs": {
    "raw_images": "raw_images",
    "filtered_images": "filtered_images",
    "polygons": "polygons",
    "exports": "exports"
  }
}
```

### B. `<stem>_<sha12>_polygons.json` (Polygon Session Format)
```json
{
  "image_filename": "10.0_P5112664.JPG",
  "image_sha256": "736bc28c75cd...",
  "image_width": 4000,
  "image_height": 3000,
  "quadrat_corners": [[312, 185], [3740, 210], [3790, 2820], [280, 2795]],
  "quadrat_area_cm2": 2500.0,
  "filter_mode": "combined",
  "colonies": [
    {
      "id": 1,
      "genus": "Mussismilia",
      "confidence": 0.892,
      "area_pixels": 45120,
      "area_cm2": 142.5,
      "coverage_pct": 5.7,
      "source": "bioclip_multiscale",
      "is_discarded": false,
      "bioclip_feature": [0.041, -0.012, "... 512 floats ..."],
      "polygons": [
        [[1200, 1400], [1250, 1420], [1280, 1490], "..."]
      ]
    }
  ]
}
```

### C. `project_ecological_summary.csv` (Consolidated Ecological Metrics)
Consolidates all SHA-256 verified images in the project with:
* `image_name`, `image_sha256_short`
* `quadrat_area_cm2`, `total_coral_cm2`, `total_coral_cover_pct`
* Genus breakdown columns: `Mussismilia_cm2`, `Mussismilia_pct`, `Porites_cm2`, `Porites_pct`, etc.

---

## 5. Development Guidelines & Best Practices

1. **Backend Execution**:
   Always run Python with the virtual environment at `d:\coralnet-inference\.venv\Scripts\python.exe`.
   ```powershell
   & "d:\coralnet-inference\.venv\Scripts\python.exe" app.py
   ```

2. **Windows Path & Character Encodings**:
   * Use UTF-8 for reading and writing files.
   * Standard output logging on Windows CP1252 should handle unicode characters safely (use `log_event()` which includes fallback for non-ASCII console characters).
   * File dialogs must be spawned as isolated subprocesses (`python -c "import tkinter.filedialog..."`) to avoid blocking Flask's event loop.

3. **Frontend DOM Sync**:
   * `<select id="image-select">` is kept hidden (`display: none;`) to synchronize active selection across all JavaScript routines.
   * The visible list is `#photo-checklist-container` / `#photo-checklist-items`.
   * Canvas height should adhere to `calc(100vh - 175px)` so that toolbar, canvas, and layout fit within standard desktop and laptop viewports without vertical overflow.

4. **Testing Changes**:
   Before committing, run an automated end-to-end verification script testing:
   - Project creation outside repo.
   - SHA-256 hash validation & mismatch detection.
   - Batch pipeline execution on pending/selected items.
   - Consolidated CSV export.
