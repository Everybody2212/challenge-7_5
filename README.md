# 🍔 Challenge 7: Unsupervised Domain Adaptation (Real → Infograph)
### 👥 Group 5 | Machine Learning & Deep Learning Retrospective
**Universidad Distrital Francisco José de Caldas** *Faculty of Engineering*

---

## 👥 Team Members

| Name | Student Code | Email / Affiliation |
| :--- | :---: | :--- |
| **Barrera Mosquera** Jairo Arturo | 20222020142 | Universidad Distrital F.J.C. |
| **Barriga Gamez** Carlos Alberto | 20222020179 | Universidad Distrital F.J.C. |
| **Arenas Gutierrez** Anderson David | 20231020030 | Universidad Distrital F.J.C. |

---

## 📊 Project Overview

This repository contains the complete pipeline for solving **Challenge 7: Domain Adaptation**. The core objective is to mitigate the drastic performance drop ($\Delta_{shift}$) that occurs when a Deep Convolutional Network trained on real-world photos (**Source Domain**) is evaluated on vector infographics (**Target Domain**). 

### 🍇 Target Subspace: Food Category
Our team (Group 5) evaluated a 6-class classification problem using a subset of the **DomainNet** dataset:
* `apple`, `banana`, `cake`, `pizza`, `sandwich`, and `strawberry`.

### 🧠 Core Methodology
1. **Baseline Setup (Part A):** Transfer Learning using a pre-trained `ResNet-18` backbone, comparing Feature Extraction ($M1$) vs. Full Fine-Tuning ($M2$).
2. **Data Generation via Neural Style Transfer (Part B):** Development of a style-transfer engine running on Gatys' canon optimization with an **L-BFGS** optimizer. It merges the semantic geometry of real food with the flat texture/chromatic distribution of the infographics domain, creating 180 synthetic training images (30 per class).
3. **Domain Adaptation (Part C):** Evaluating performance under three independent random seeds (**42, 100, 2026**) comparing traditional *Few-Shot Fine-Tuning* ($M4$) against our proposed *NST-Augmentation Strategy* ($M5$).

---

## 🗂️ Repository Structure

The project directory is meticulously structured to separate data assets, logging logs, metrics, and production source files:

```text
CHALLENGE-7_5/
│
├── checkpoints/                  # Trained model state dicts
│   ├── best_part_A_model.pt      # Source-domain baseline weights
│   └── best_part_C_model.pt      # Adapted domain champion weights
│
├── data/                         # Data layer
│   ├── source_real/              # Original photography (Source)
│   ├── target_infograph/         # Original vector art files (Target)
│   ├── synthetic_target/         # 180 stylized images generated via NST engine
│   ├── model_final_adapted.pth   
│   └── model_stage1_source.pth   
│
├── figures/                      # Project artifact figures required for IEEE paper
│   ├── figure1_curves_part_A.pdf # Loss and Accuracy convergence curves
│   ├── figure2_gallery_side_by_side.pdf # Content vs. Style vs. NST Synthesized output matrix
│   ├── figure3_gradcam_attention.png    # Attention maps (Aciertos/Fallos via Grad-CAM)
│   └── figure4_tsne_projection.png      # Latent space geometry using t-SNE reduction
│
├── runs/                         # TensorBoard event logs (All 3 seeds organized dynamically)
│
├── src/                          # Production source scripts
│   ├── classifier.py             # Part A training engine
│   ├── dataset_loader.py         # Custom PyTorch Dataset pipelines and transforms
│   ├── domain_adaptation.py      # Part C domain adaptation runs (M4 & M5)
│   ├── organizar_dataset.py      # File system management and train/test partitioners
│   └── style_transfer.py         # Neural Style Transfer core engine (L-BFGS + DirectML)
│
├── CHECKLIST.md                  # Detailed metrics table, hyperparameters, and executive summary
├── INSTRUCTIONS.md               # Strict execution command lines for replication
├── requirements.txt              # Standardized environment scientific dependencies
│
└── Part_[A/B/C]_...ipynb         # Interactive verification Jupyter Notebooks


## 📈 Summary of Experimental Variants

Our experimental setup evaluated the following network variants across three independent runs:

- **$M1$ (Feature Extraction):** Backbone parameters are frozen. Only the modified fully connected (`fc`) classification layer (**3,078 parameters**) is trained on real photos.
- **$M2$ (Full Source Fine-Tuning):** The entire network (**~11.1M parameters**) is fine-tuned end-to-end on real photos.
- **$M2$ Cross-Evaluation:** The trained $M2$ model is evaluated directly on the target **Infograph** domain without adaptation. This serves as the lower-bound performance and isolates the pure domain shift penalty ($\Delta_{shift}$).
- **$M4$ (Few-Shot Target Fine-Tuning):** The network is fine-tuned directly on a small subset of real Infograph images.
- **$M5$ (NST Augmentation):** The model is trained with the augmented hybrid dataset (**Real Photos + NST-synthesized images**). This strategy achieved a **Net Accuracy Gain of +8.26%** over the unadapted cross-evaluation baseline.

---

## 🚀 Getting Started & Replication

To reproduce the full execution matrix, model checkpoints, and figures locally, follow the terminal instructions documented in:

- [`INSTRUCTIONS.md`](INSTRUCTIONS.md) — complete replication commands
- [`CHECKLIST.md`](CHECKLIST.md) — experimental results matrix, training curves, numerical statistics ($\mu \pm \sigma$), and final report summary
