# Wi-Fi CSI-Based Indoor Occupancy Detection

A research project exploring the use of **Wi-Fi Channel State Information (CSI)** for indoor occupancy detection using ESP32-based receivers and signal analysis.

The primary objective is to investigate whether changes in Wi-Fi signals can be used to determine whether an indoor environment is **empty or occupied**, without requiring cameras or dedicated wearable devices.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Experimental Setup](#experimental-setup)
- [Dataset Organization](#dataset-organization)
- [Repository Structure](#repository-structure)
- [Data Processing and Analysis](#data-processing-and-analysis)
- [Occupancy Detection](#occupancy-detection)
- [Installation and Requirements](#installation-and-requirements)
- [Running the Analysis](#running-the-analysis)
- [Current Progress](#current-progress)
- [Future Work](#future-work)

---

## Project Overview

Wi-Fi signals propagate through indoor environments and interact with objects, walls, furniture, and human bodies. The presence and movement of people can influence the characteristics of received wireless signals.

**Channel State Information (CSI)** provides information about the wireless channel across individual subcarriers. These measurements can potentially capture environmental changes that are useful for occupancy detection.

This project investigates the feasibility of using CSI measurements collected through ESP32-based receiver nodes to distinguish between empty and occupied indoor environments.

The project follows an experimental approach involving:

1. Collecting Wi-Fi CSI measurements under different occupancy conditions.
2. Organizing and validating the collected dataset.
3. Analysing CSI and RSSI characteristics.
4. Investigating signal consistency across repeated experiments.
5. Extracting features from the collected measurements.
6. Training and evaluating machine-learning models for binary occupancy detection.

## Objectives

- Develop a Wi-Fi CSI-based indoor occupancy detection prototype.
- Collect CSI measurements under different room occupancy conditions.
- Study variations in CSI and RSSI measurements.
- Investigate the consistency and repeatability of collected signal measurements.
- Identify useful CSI subcarrier features.
- Evaluate whether CSI measurements can distinguish empty and occupied environments.
- Compare different machine-learning approaches for occupancy classification.

## Experimental Setup

The experiments were conducted using ESP32-based receiver nodes placed inside indoor environments.

The dataset currently contains measurements from two experimental rooms, with two receiver positions associated with each room.

| Parameter | Configuration |
|---|---|
| Experimental environments | Room A and Room B |
| Receivers | Rx1 and Rx2 |
| Receiver hardware | ESP32-based nodes |
| Wireless technology | Wi-Fi |
| Main signal measurement | Channel State Information (CSI) |
| Additional measurement | Received Signal Strength Indicator (RSSI) |
| Experimental cases | C1–C8 |
| Repetitions per case | 8 |
| Recording duration | 120 seconds per experiment |
| Detection objective | Binary occupancy classification |

### Experimental Conditions

The eight experimental cases represent different occupancy conditions, including empty-room, sitting, movement, and multiple-person scenarios.

The current binary classification mapping is:

| Case | Experimental condition | Label |
|---|---|---|
| C1 | Empty room | 0 – Empty |
| C2 | One person sitting | 1 – Occupied |
| C3 | One person walking | 1 – Occupied |
| C4 | One person sitting with hand movement | 1 – Occupied |
| C5 | Two people sitting | 1 – Occupied |
| C6 | Two people moving | 1 – Occupied |
| C7 | Three people sitting | 1 – Occupied |
| C8 | Three people moving | 1 – Occupied |

*Note: The case descriptions and labels should be checked against the final experiment protocol and metadata before publication.*

---

## Dataset Organization

The collected dataset is organized into two main categories:

- **raw_packets:** Packet-level CSI measurements and associated signal information.
- **window_summary:** Time-window-based signal summaries generated from the collected packet measurements.

The original experimental recordings are maintained separately from the organized dataset.

### Original Dataset

```text
BTP_Data/
└── CSI_Occupancy_Dataset/
    ├── RoomA_Rx1/
    ├── RoomA_Rx2/
    ├── RoomB_Rx1/
    └── RoomB_Rx2/
```

Each room-receiver directory contains the experimental recordings organized by test case and repetition.

### Organized Dataset

```text
OrganizedDataset/
│
├── raw_packets/
│
├── window_summary/
│
├── batch_repeatability_results/
│   ├── plots/
│   └── repeatability_summary_matrix.csv
│
├── csi_analysis/
│
├── null_subcarrier_analysis/
│
├── occupancy_model_results/
│
├── rssi_analysis/
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

### CSV File Description

**Raw packet CSV files**

These contain packet-level measurements, including:

- Packet sequence and timestamp information.
- RSSI measurements.
- Wi-Fi channel information.
- CSI length and CSI data.
- Source MAC address.
- Mean CSI amplitude and subcarrier measurements.

**Window summary CSV files**

These contain time-window-based signal statistics, including:

- Window timestamp or second index.
- Packet count.
- Mean and standard deviation of RSSI.
- Mean and standard deviation of CSI amplitude.
- Subcarrier-wise summary measurements.

The window summary data is used for signal analysis and feature extraction during occupancy modelling.

---

## Repository Structure

The following represents the current project layout:

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
│   │   │
│   │   ├── csv_dataset_manifest.csv
│   │   ├── csi_global_subcarrier_summary.csv
│   │   ├── csi_subcarrier_recording_statistics.csv
│   │   ├── packet_gap_analysis.csv
│   │   ├── raw_repetition_validation.csv
│   │   ├── raw_structure_validation.csv
│   │   ├── recording_quality_report.csv
│   │   ├── rssi_recording_statistics.csv
│   │   ├── summary_repetition_validation.csv
│   │   └── summary_structure_validation.csv
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
│   └── RoomB_MultiReceiver_Occupancy_Analysis...
│
└── README.md
```

### Python Scripts

The following scripts are part of the Room A analysis workflow.

| Script | Purpose |
|---|---|
| `org_data.py` | Organizes the original experimental recordings into structured raw-packet and window-summary datasets. |
| `dataset_check.py` | Checks dataset organization, file availability, and structural consistency. |
| `basic_stats.py` | Performs basic statistical analysis of collected measurements. |
| `all_signals.py` | Analyses signal characteristics across the collected recordings. |
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
- Validating raw packet and window summary datasets.

### 2. CSI Analysis

CSI measurements are investigated to understand how wireless channel characteristics vary under different indoor conditions.

The analysis includes:

- CSI subcarrier measurements.
- Subcarrier-wise statistics.
- CSI amplitude and signal profiles.
- Comparison across different experimental cases.
- Comparison across repeated recordings.
- Identification of permanently zero-valued stored subcarrier columns.

### 3. Null Subcarrier Analysis

The collected CSI dataset is examined to identify subcarrier columns that consistently contain zero values.

This helps identify inactive or unusable stored features before subsequent analysis.

The observed zero-valued columns are treated as dataset-level observations; their exact physical subcarrier interpretation requires verification against the CSI extraction and parsing implementation.

### 4. RSSI Analysis

RSSI measurements are analysed independently to understand their variation across:

- Experimental cases.
- Room and receiver combinations.
- Repeated experiments.
- Individual recordings.

The results are used to understand whether RSSI alone provides useful information for occupancy detection.

### 5. Repeatability Analysis

Repeated experiments are compared to investigate whether similar experimental conditions produce reasonably consistent signal characteristics.

This includes examining signal statistics and variations across repetitions.

---

## Occupancy Detection

The main objective of the machine-learning stage is to classify an indoor environment into one of two categories:

| Class | Meaning | Label |
|---|---|---|
| Empty | No person present | 0 |
| Occupied | One or more people present | 1 |

### Initial Machine-Learning Experiment

The initial modelling experiment uses data collected from:

- Room A
- Receiver Rx2
- A single Wi-Fi access point
- Eight experimental cases
- Eight repetitions per case

This gives 64 recordings for the initial experiment.

### Feature Extraction

Features are extracted from the window summary CSV files.

The initial experiment uses 5-second non-overlapping windows.

The feature groups include:

**CSI features**
- Mean values of selected CSI subcarrier measurements.
- Standard deviations of selected CSI subcarrier measurements.

**RSSI features**
- Mean RSSI.
- Temporal variation in RSSI.
- Average within-second RSSI standard deviation.

Additional signal summary features are included in the combined CSI + RSSI experiment.

### Models Evaluated

The initial model comparison includes:

- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

Three feature configurations are investigated:

1. CSI-only
2. RSSI-only
3. CSI + RSSI

Class weighting and undersampling are also investigated to address the imbalance between empty and occupied windows.

### Initial Evaluation Results

The initial RoomA-Rx2 experiment produced the following results using class weighting:

| Model | CSI-only accuracy | RSSI-only accuracy |
|---|---:|---:|
| Logistic Regression | 90.81% | 87.93% |
| Random Forest | 98.69% | 92.65% |
| SVM | 99.48% | 88.71% |

The initial results indicate that CSI features provide stronger occupancy classification performance than RSSI features alone in this experimental setup.

The CSI-only SVM achieved the highest initial test accuracy of **99.48%**.

These are preliminary window-level results from a held-out repetition split, not final validated system performance. Further recording-level and independent-session evaluation is required.

### Evaluation Strategy

The modelling workflow uses a repetition-based split:

| Dataset | Repetitions |
|---|---|
| Training | Rep01–Rep05 |
| Validation | Rep06 |
| Testing | Rep07–Rep08 |

All windows belonging to a particular recording are kept within the same split.

Evaluation metrics include:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix

Further evaluation investigates recording-level predictions and consistency across held-out repetitions.

---

## Installation and Requirements

### Prerequisites

- Python 3.10 or later (recommended).
- Visual Studio Code or another Python development environment.
- Git.
- Required Python libraries.

### Clone the Repository

```bash
git clone https://github.com/Charan060706/BTP-Analysis
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

The current analysis scripts use Python data-analysis and machine-learning libraries.

```bash
pip install numpy pandas matplotlib seaborn scikit-learn
```

If additional dependencies are required by individual scripts, install them as needed.

---

## Running the Analysis

Run the Python scripts from the appropriate project directory.

For example:

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

Run the initial occupancy detection experiment:

```bash
python occ_mod_exp.py
```

**Important:** Some scripts depend on the directory structure and file paths used during the original experiments. Update their input and output paths if running them in a different environment.

---

## Current Progress

The following stages have been completed or initially investigated:

- [x] Experimental data collection across two rooms and two receiver positions.
- [x] Organization of raw packet and window summary CSV files.
- [x] Dataset structural validation.
- [x] Repetition count verification.
- [x] Recording quality and packet interval analysis.
- [x] CSI signal and subcarrier analysis.
- [x] Identification of permanently zero-valued stored subcarrier columns.
- [x] Initial RSSI statistical analysis.
- [x] Initial repeatability analysis.
- [x] Initial CSI-only, RSSI-only, and combined feature experiments.
- [x] Initial comparison of Logistic Regression, Random Forest, and SVM.
- [ ] Recording-level model evaluation.
- [ ] Further repetition-wise validation.
- [ ] Evaluation across independent collection sessions.
- [ ] Validation across different rooms and receiver configurations.
- [ ] Final model selection and system-level evaluation.

---

## Future Work

The next stages of the project include:

1. Complete recording-level evaluation of the trained occupancy models.
2. Investigate model consistency across different experimental repetitions.
3. Study the effect of different CSI feature extraction strategies.
4. Compare different temporal window sizes.
5. Evaluate the impact of different receiver positions and access points.
6. Investigate model generalization across rooms and independent collection sessions.
7. Finalize a suitable model for binary indoor occupancy detection.

---

## Project Scope

The current scope focuses on **binary indoor occupancy detection**, determining whether an indoor environment is empty or occupied.

The project does not currently aim to identify individuals or perform person identification. Occupancy counting and detailed human activity recognition are outside the primary scope of the current prototype.

---

## Acknowledgements

This project is being carried out as part of the Bachelor of Technology Project (BTP).

**Institution:** Indian Institute of Technology Tirupati (IIT Tirupati)

