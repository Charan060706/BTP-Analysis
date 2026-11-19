# Wi-Fi CSI-Based Indoor Occupancy Detection

A research project investigating the use of **Wi-Fi Channel State Information (CSI)** for indoor occupancy detection using ESP32-based receiver nodes.

The primary objective is to determine whether changes in Wi-Fi channel characteristics can be used to identify whether an indoor environment is **empty or occupied**, without relying on cameras or wearable devices.

**GitHub Repository:** [Charan060706/BTP-Analysis](https://github.com/Charan060706/BTP-Analysis)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Experimental Setup](#experimental-setup)
- [Dataset Organization](#dataset-organization)
- [Repository Structure](#repository-structure)
- [Room A: Single-Access-Point Analysis](#room-a-single-access-point-analysis)
- [Room B: Dual-Access-Point Multi-Receiver Analysis](#room-b-dual-access-point-multi-receiver-analysis)
- [Data Processing and Analysis](#data-processing-and-analysis)
- [Occupancy Detection](#occupancy-detection)
- [Installation and Requirements](#installation-and-requirements)
- [Running the Analysis](#running-the-analysis)
- [Current Progress](#current-progress)
- [Future Work](#future-work)

---

## Project Overview

Wi-Fi signals propagate through indoor environments and interact with walls, furniture, objects, and human bodies. The presence and movement of people can influence the characteristics of received wireless signals.

**Channel State Information (CSI)** provides information about the wireless channel across individual subcarriers. These measurements can potentially capture environmental changes that are useful for indoor occupancy detection.

This project investigates the feasibility of using CSI measurements collected through ESP32-based receiver nodes to distinguish between empty and occupied indoor environments.

The project follows an experimental approach involving two different indoor environments:

- **Room A:** A single-access-point environment.
- **Room B:** A dual-access-point environment using two receivers connected to separate access points, with their measurements fused for multi-receiver analysis.

The overall workflow includes:

1. Collecting Wi-Fi CSI measurements under different occupancy conditions.
2. Organizing and validating the collected dataset.
3. Analysing CSI and RSSI characteristics.
4. Investigating signal consistency across repeated experiments.
5. Extracting useful features from the collected measurements.
6. Training and evaluating machine-learning models.
7. Comparing single-receiver and multi-receiver occupancy detection approaches.

## Objectives

- Develop a Wi-Fi CSI-based indoor occupancy detection prototype.
- Collect CSI measurements under different room occupancy conditions.
- Study variations in CSI and RSSI measurements.
- Investigate signal consistency and repeatability across experiments.
- Identify useful CSI subcarrier features.
- Evaluate whether CSI measurements can distinguish empty and occupied environments.
- Investigate the contribution of multiple receivers through feature-level fusion.
- Compare different machine-learning approaches for binary occupancy classification.

---

## Experimental Setup

The experiments use ESP32-based receiver nodes placed inside indoor environments to collect Wi-Fi CSI measurements.

Two experimental environments are considered.

| Parameter | Room A | Room B |
|---|---|---|
| Environment | Classroom | Computer laboratory |
| Access points | 1 | 2 |
| Receivers | Rx1 and Rx2 | Rx1 and Rx2 |
| Receiver association | Same AP | Separate APs |
| Analysis approach | Initial modelling with Rx2 | Individual receiver and fused receiver analysis |
| Main objective | Single-receiver occupancy detection | Multi-receiver occupancy detection |

### Common Experimental Conditions

The same eight occupancy scenarios are considered in both rooms.

| Case | Experimental condition | People | Label |
|---|---|---:|---|
| C1 | Empty room | 0 | 0 – Empty |
| C2 | One person sitting | 1 | 1 – Occupied |
| C3 | One person walking | 1 | 1 – Occupied |
| C4 | One person sitting with hand movement | 1 | 1 – Occupied |
| C5 | Two people sitting | 2 | 1 – Occupied |
| C6 | One person sitting and one walking | 2 | 1 – Occupied |
| C7 | Three people sitting | 3 | 1 – Occupied |
| C8 | Three people with random movement | 3 | 1 – Occupied |

The primary classification task is binary occupancy detection:

- `0` represents an empty environment.
- `1` represents an occupied environment.

---

## Dataset Organization

The project maintains the original collected measurements separately from the processed datasets and analysis outputs.

### Room A Dataset

The original Room A experimental recordings are maintained in separate directories for each receiver.

```text
BTP_Data/
└── CSI_Occupancy_Dataset/
    ├── RoomA_Rx1/
    ├── RoomA_Rx2/
    ├── RoomB_Rx1/
    └── RoomB_Rx2/
```

The organized Room A dataset contains:

- `raw_packets/` – Packet-level CSI and RSSI measurements.
- `window_summary/` – Time-based signal summary measurements.

### Room B Dataset

Room B uses a fused dataset containing measurements from both receivers.

```text
BTP_analysis_RoomB/
│
├── RoomB_FUSED.zip
│
└── RoomB_MultiReceiver_Occupancy_Analysis.ipynb
```

The ZIP archive contains 64 fused recording files organized by experimental case and repetition.

Expected structure:

```text
RoomB_FUSED/
│
├── C1/
│   ├── Rep01/
│   │   └── Fused_window_summary.csv
│   ├── Rep02/
│   └── ...
│
├── C2/
├── C3/
├── C4/
├── C5/
├── C6/
├── C7/
└── C8/
```

Each `Fused_window_summary.csv` contains time-indexed measurements from both receivers, including receiver-specific CSI, RSSI, CSI amplitude, packet count, and receiver-presence information.

The common `second` column allows measurements from both receivers to be processed within corresponding time windows.

### Room A Organized Dataset

```text
OrganizedDataset/
│
├── batch_repeatability_results/
│   ├── plots/
│   └── repeatability_summary_matrix.csv
│
├── csi_analysis/
├── null_subcarrier_analysis/
├── occupancy_model_results/
├── raw_packets/
├── rssi_analysis/
├── window_summary/
│
├── csv_dataset_manifest.csv
├── csi_global_subcarrier_summary.csv
├── csi_subcarrier_recording_statistics.csv
├── packet_gap_analysis.csv
├── raw_repetition_validation.csv
├── raw_structure_validation.csv
├── recording_quality_report.csv
├── rssi_recording_statistics.csv
├── summary_repetition_validation.csv
└── summary_structure_validation.csv
```

---

## Repository Structure

```text
BTP-Analysis/
│
├── .vscode/
│
├── BTP_analysis_RoomA/
│   │
│   ├── BTP_Data/
│   │   └── CSI_Occupancy_Dataset/
│   │       ├── RoomA_Rx1/
│   │       ├── RoomA_Rx2/
│   │       ├── RoomB_Rx1/
│   │       └── RoomB_Rx2/
│   │
│   ├── OrganizedDataset/
│   │   ├── batch_repeatability_results/
│   │   ├── csi_analysis/
│   │   ├── null_subcarrier_analysis/
│   │   ├── occupancy_model_results/
│   │   ├── raw_packets/
│   │   ├── rssi_analysis/
│   │   ├── window_summary/
│   │   └── analysis_reports.csv
│   │
│   ├── all_signals.py
│   ├── basic_stats.py
│   ├── case_null_sub.py
│   ├── csi_prof_any.py
│   ├── dataset_check.py
│   ├── exp_rep_ver.py
│   ├── intervals.py
│   ├── null_subc_viz.py
│   ├── occ_mod_exp.py
│   ├── org_data.py
│   ├── rssi_casewise.py
│   ├── rssi_rep_analysis.py
│   ├── signal_insp.py
│   └── verify_repetition.py
│
├── BTP_analysis_RoomB/
│   ├── RoomB_FUSED.zip
│   └── RoomB_MultiReceiver_Occupancy_Analysis.ipynb
│
└── README.md
```

---

## Room A: Single-Access-Point Analysis

Room A represents the initial single-access-point experimental setup.

A Wi-Fi access point is placed inside the room, and two ESP32-based receivers collect CSI measurements from the wireless environment.

The initial machine-learning experiment focuses on **Rx2 only**, providing a single-receiver baseline for occupancy detection.

### Room A Analysis Workflow

1. Organize raw packet-level and window-summary CSV files.
2. Validate the dataset structure and repetition counts.
3. Analyse CSI and RSSI characteristics.
4. Investigate permanently zero-valued stored subcarrier columns.
5. Compare signal characteristics across experimental cases.
6. Investigate repeatability across recordings.
7. Extract CSI and RSSI features.
8. Train and evaluate occupancy classification models.

### Python Scripts

| Script | Purpose |
|---|---|
| `org_data.py` | Organizes original experimental recordings into structured raw-packet and window-summary datasets. |
| `dataset_check.py` | Checks dataset organization, file availability, and structural consistency. |
| `basic_stats.py` | Performs basic statistical analysis of collected measurements. |
| `all_signals.py` | Analyses signal characteristics across collected recordings. |
| `intervals.py` | Investigates packet timing and inter-packet intervals. |
| `signal_insp.py` | Performs signal-level inspection of collected measurements. |
| `verify_repetition.py` | Checks consistency across repeated experiments. |
| `exp_rep_ver.py` | Supports experimental repetition verification and analysis. |
| `case_null_sub.py` | Analyses permanently zero-valued subcarrier columns across experimental cases. |
| `null_subc_viz.py` | Generates visualizations related to null subcarrier measurements. |
| `csi_prof_any.py` | Performs CSI profile analysis for selected recordings or experimental cases. |
| `rssi_casewise.py` | Analyses and compares RSSI measurements across experimental cases. |
| `rssi_rep_analysis.py` | Investigates RSSI consistency across repeated experiments. |
| `occ_mod_exp.py` | Runs machine-learning experiments for binary occupancy detection using CSI and RSSI features. |

### Initial Room A Modelling Results

The initial RoomA-Rx2 modelling experiment uses 64 recordings from eight experimental cases and eight repetitions.

The dataset is divided by repetition:

| Dataset | Repetitions |
|---|---|
| Training | Rep01–Rep05 |
| Validation | Rep06 |
| Testing | Rep07–Rep08 |

The initial class-weighted results are:

| Model | CSI-only accuracy | RSSI-only accuracy |
|---|---:|---:|
| Logistic Regression | 90.81% | 87.93% |
| Random Forest | 98.69% | 92.65% |
| SVM | 99.48% | 88.71% |

The initial results indicate that CSI features provide stronger occupancy classification performance than RSSI features alone in this experimental setup.

The CSI-only SVM achieved the highest initial test accuracy of **99.48%**.

These are preliminary window-level results from a held-out repetition split. Recording-level and independent-session evaluation are still required before claiming generalization.

---

## Room B: Dual-Access-Point Multi-Receiver Analysis

Room B represents the multi-access-point experimental setup conducted in the computer laboratory.

Unlike Room A, which uses a single access point, Room B uses **two separate Wi-Fi access points and two ESP32-based receivers**.

### Room B Network Configuration

The two receivers are connected to different access points:

| Component | Connection |
|---|---|
| Router 1 / AP1 | Receiver Rx1 |
| Router 2 / AP2 | Receiver Rx2 |

Each receiver collects CSI and RSSI measurements from its associated access point.

Both receivers collect measurements during the same experimental recordings. Their measurements are then aligned and combined into a common fused dataset.

This setup allows the project to investigate whether information from multiple receiver-access-point links can improve indoor occupancy detection.

### Multi-Receiver Data Fusion

The Room B dataset contains fused measurements from Rx1 and Rx2.

Instead of analysing only one receiver, the fused dataset preserves receiver-specific measurements and combines their extracted features for modelling.

The fusion workflow involves:

1. Collecting measurements independently through Rx1 and Rx2.
2. Preparing time-indexed summary measurements for both receivers.
3. Aligning measurements using the common time index (`second`).
4. Retaining receiver-specific CSI, RSSI, amplitude, and packet-count information.
5. Tracking receiver data availability through presence indicators.
6. Extracting features from corresponding five-second windows.
7. Combining the feature vectors from both receivers for fused modelling.

**Important:** The two receivers' CSI measurements are not averaged together. Their features are concatenated, preserving the information contributed by each receiver.

### Room B Dataset Details

| Parameter | Configuration |
|---|---|
| Experimental environment | Computer laboratory |
| Access points | 2 |
| Receivers | 2 ESP32-based nodes |
| Receiver 1 | Connected to AP1 |
| Receiver 2 | Connected to AP2 |
| Experimental cases | C1–C8 |
| Repetitions | Rep01–Rep08 |
| Fused recordings | 64 |
| Input dataset | `RoomB_FUSED.zip` |
| Summary file | `Fused_window_summary.csv` |

### Room B Analysis Notebook

The complete Room B analysis is implemented in:

`RoomB_MultiReceiver_Occupancy_Analysis.ipynb`

The notebook is designed to run in Google Colab or a local Jupyter environment.

It contains the following stages:

**1. Dataset upload and extraction**

- Uploads `RoomB_FUSED.zip`.
- Extracts the fused dataset.
- Checks the expected case and repetition directory structure.

**2. Dataset inspection and validation**

- Checks the availability of all 64 recordings.
- Verifies required receiver-specific columns.
- Checks duplicate time indices and missing values.
- Inspects recording lengths and receiver-presence information.

**3. Five-second feature extraction**

The notebook creates non-overlapping five-second windows using the common `second` index.

For each receiver, it extracts:

- CSI subcarrier means and standard deviations.
- Mean RSSI.
- Temporal standard deviation of RSSI.
- Mean per-second RSSI standard deviation.
- Mean CSI amplitude.
- Temporal standard deviation of CSI amplitude.
- Mean packet count.
- Receiver observed-seconds and observed-fraction indicators.

If one receiver has no observations in a particular window, its measurement features are left missing and handled during model preprocessing. This allows the available receiver's measurements to remain usable.

**4. Feature configurations**

The notebook compares nine feature configurations:

| Receiver configuration | Feature sets |
|---|---|
| RX1-only | CSI-only, RSSI-only, CSI + RSSI |
| RX2-only | CSI-only, RSSI-only, CSI + RSSI |
| Fused RX1 + RX2 | CSI-only, RSSI-only, CSI + RSSI |

For the fused configurations, receiver-specific feature vectors are concatenated rather than averaged.

**5. Class balancing**

Two training strategies are investigated:

- `Class_weighting`: Uses the original training distribution with balanced class weights.
- `Undersampling`: Retains empty-class training windows and samples occupied windows across the occupied experimental cases.

Validation and test data are not undersampled.

**6. Machine-learning models**

The following classifiers are evaluated:

- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

The notebook uses preprocessing pipelines with median imputation. Feature scaling is applied for Logistic Regression and SVM.

**7. Model selection and evaluation**

The repetition-based split is:

| Dataset | Repetitions |
|---|---|
| Training | Rep01–Rep05 |
| Validation | Rep06 |
| Testing | Rep07–Rep08 |

For each feature configuration, candidate models are compared using validation macro-F1. The best candidate is then evaluated on the held-out test repetitions.

This makes it possible to compare:

- RX1-only performance.
- RX2-only performance.
- Fused RX1 + RX2 performance.

**8. Additional prediction and model export**

The notebook also includes:

- Exporting the selected fused model as a `.joblib` artifact.
- Saving the required feature-column information and label mapping.
- A prediction function for new fused recordings.
- Manual testing examples for empty and occupied recordings.
- Classification reports and confusion matrices.
- Exporting the analysis results as CSV files and a ZIP archive.

### Room B Output Files

The notebook generates an analysis directory containing outputs such as:

| Output | Description |
|---|---|
| `all_receiver_features.csv` | Extracted feature dataset for both receivers. |
| `validation_model_comparison.csv` | Validation performance of candidate models. |
| `final_test_comparison.csv` | Final held-out test comparison across configurations. |
| `model_comparison.csv` | Consolidated model comparison output. |
| `*_classification_report.csv` | Classification metrics for individual configurations. |
| `*_confusion_matrix.png` | Confusion matrices for model evaluation. |
| `best_fused_occupancy_model.joblib` | Saved selected fused occupancy model. |
| `RoomB_Analysis_Results.zip` | Packaged analysis outputs. |

The exact generated files depend on the notebook execution.

### Purpose of Room B Experiments

The Room B experiment extends the single-receiver analysis conducted in Room A.

It investigates whether using two independently collected Wi-Fi links can provide more useful information for occupancy detection than relying on one receiver alone.

The main comparison is:

**RX1-only vs RX2-only vs Fused RX1 + RX2**

This allows us to investigate the contribution of multiple receivers and the potential benefits of multi-receiver feature fusion.

---

## Data Processing and Analysis

The project follows multiple stages of data analysis before model training.

### 1. Dataset Organization and Validation

The collected recordings are organized into structured directories and CSV files.

Validation includes:

- Checking the number of recordings.
- Verifying expected experimental cases and repetitions.
- Checking missing or unreadable CSV files.
- Comparing CSV structures and column availability.
- Validating raw packet and window-summary datasets.

### 2. CSI Analysis

CSI measurements are investigated to understand how wireless channel characteristics vary under different indoor conditions.

The analysis includes:

- CSI subcarrier measurements.
- Subcarrier-wise statistics.
- CSI amplitude profiles.
- Comparison across experimental cases.
- Comparison across repeated recordings.
- Identification of permanently zero-valued stored subcarrier columns.

### 3. Null Subcarrier Analysis

The collected CSI dataset is examined to identify subcarrier columns that consistently contain zero values.

This helps identify inactive or unusable stored features before subsequent analysis.

The exact physical subcarrier interpretation requires verification against the CSI extraction and parsing implementation.

### 4. RSSI Analysis

RSSI measurements are analysed independently to understand their variation across:

- Experimental cases.
- Room and receiver combinations.
- Repeated experiments.
- Individual recordings.

The results help determine whether RSSI alone provides useful information for occupancy detection.

### 5. Repeatability Analysis

Repeated experiments are compared to investigate whether similar experimental conditions produce reasonably consistent signal characteristics.

This includes examining signal statistics and variations across repetitions.

### 6. Multi-Receiver Fusion Analysis

The Room B dataset is used to study the combination of signal features from two independent receiver-access-point links.

Individual receiver performance is compared with the fused feature representation to investigate the contribution of multi-receiver sensing.

---

## Occupancy Detection

The primary objective of the machine-learning stage is to classify an indoor environment into one of two categories.

| Class | Meaning | Label |
|---|---|---|
| Empty | No person present | 0 |
| Occupied | One or more people present | 1 |

### Feature Extraction

The modelling workflow uses five-second non-overlapping windows.

Features include:

**CSI features**
- Mean values of selected CSI subcarrier measurements.
- Standard deviations of selected CSI subcarrier measurements.

**RSSI features**
- Mean RSSI.
- Temporal variation in RSSI.
- Average within-second RSSI standard deviation.

**Additional signal features**
- CSI amplitude statistics.
- Packet-count statistics.
- Receiver observation and availability information in the Room B fused experiment.

### Models Evaluated

- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

### Evaluation Metrics

The models are evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Macro-F1
- Confusion matrices

The evaluation uses repetition-based splitting to avoid distributing windows from the same recording across training and testing sets.

---

## Installation and Requirements

### Prerequisites

- Python 3.10 or later (recommended).
- Visual Studio Code or another Python development environment.
- Git.
- Google Colab or Jupyter Notebook for the Room B notebook.

### Clone the Repository

```bash
git clone https://github.com/Charan060706/BTP-Analysis.git
cd BTP-Analysis
```

### Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install numpy pandas matplotlib seaborn scikit-learn jupyter joblib
```

Additional libraries may be required by individual scripts or notebooks.

---

## Running the Analysis

### Room A

Navigate to the Room A directory:

```bash
cd BTP_analysis_RoomA
```

Organize the dataset:

```bash
python org_data.py
```

Validate the dataset:

```bash
python dataset_check.py
```

Perform signal analysis:

```bash
python all_signals.py
```

Investigate CSI subcarriers:

```bash
python case_null_sub.py
```

Analyse RSSI measurements:

```bash
python rssi_casewise.py
```

Run the occupancy detection experiment:

```bash
python occ_mod_exp.py
```

### Room B

Navigate to the Room B directory:

```bash
cd BTP_analysis_RoomB
```

Open the notebook:

```bash
jupyter notebook RoomB_MultiReceiver_Occupancy_Analysis.ipynb
```

Alternatively, upload the notebook to Google Colab.

Upload `RoomB_FUSED.zip` when prompted and execute the notebook cells in sequence.

The notebook will extract the dataset, validate the recordings, perform feature extraction, train the candidate models, compare receiver configurations, and export the evaluation results.

**Important:** Some scripts and notebooks use paths specific to their original execution environments. Update input and output paths when running them locally or in a different environment.

---

## Current Progress

The following stages have been completed or initially investigated:

- [x] Experimental data collection across two rooms.
- [x] Single-access-point experiments in Room A.
- [x] Dual-access-point experiments in Room B.
- [x] Organization of Room A raw packet and window-summary CSV files.
- [x] Preparation of the Room B fused dataset.
- [x] Dataset structural validation.
- [x] Repetition count verification.
- [x] Recording quality and packet interval analysis.
- [x] CSI signal and subcarrier analysis.
- [x] Identification of permanently zero-valued stored subcarrier columns.
- [x] Initial RSSI statistical analysis.
- [x] Initial repeatability analysis.
- [x] Initial Room A occupancy classification experiments.
- [x] Room B multi-receiver feature extraction and modelling workflow.
- [x] RX1-only, RX2-only and fused feature configurations implemented in Room B.
- [ ] Complete recording-level evaluation.
- [ ] Further repetition-wise validation.
- [ ] Detailed comparison of Room A and Room B generalization.
- [ ] Evaluation across independent collection sessions.
- [ ] Final model selection and system-level evaluation.

---

## Future Work

The next stages of the project include:

1. Complete recording-level evaluation of the trained occupancy models.
2. Investigate model consistency across different experimental repetitions.
3. Study the effect of different CSI feature extraction strategies.
4. Compare different temporal window sizes.
5. Evaluate the contribution of individual receivers in Room B.
6. Investigate whether fused receiver features improve occupancy detection.
7. Evaluate model generalization across rooms and independent collection sessions.
8. Finalize a suitable model for binary indoor occupancy detection.

---

## Project Scope

The current scope focuses on **binary indoor occupancy detection**, determining whether an indoor environment is empty or occupied.

The project does not currently aim to identify individuals or perform person identification.

Although the experimental scenarios contain different numbers of people, all occupied cases are assigned the same binary label. Therefore, the current classification task does not estimate the number of occupants.

Occupancy counting and detailed human activity recognition are outside the primary scope of the current prototype.

---

## Acknowledgements

This project is being carried out as part of the Bachelor of Technology Project (BTP).

**Institution:** Indian Institute of Technology Tirupati (IIT Tirupati)
