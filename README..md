# IA626 Final Project  
## Multi-modal Traffic Sensor Validation Using Image and Audio Data

---

## 1. Project Summary

This project analyzes large-scale multi-modal traffic data collected from roadside sensors, combining **image files**, **audio files**, and **sensor metadata logged as newline-delimited JSON**. The primary objective is to perform a **holistic validation and exploratory analysis of multi-modal traffic sensor data**, integrating sensor-reported metadata with **independently derived audio signal metrics** and **image quality measurements**.

Rather than focusing on prediction, the project is framed as a **data validation and diagnostic analysis**, assessing system reliability, cross-modal consistency, and potential failure modes in a real-world sensing pipeline.

---

## 2. Primary Questions

### Primary Question

**Do sensor-reported measurements and file-system–derived data (audio and image) exhibit stable, interpretable, and temporally consistent relationships across modalities, and can deviations from these relationships be used to identify sensor or pipeline anomalies?**

### Secondary Questions

- **Audio consistency**  
  Is there a stable relationship between sensor-reported sound levels (dBA) and waveform-derived audio amplitude metrics?

- **Capture persistence**  
  Are there periods where sensors report activity but corresponding files are missing, sparse, or degraded?

- **Cross-modal availability**  
  How do image and audio capture rates co-vary over time, and are there systematic imbalances between modalities?

- **Image quality stability**  
  Do image quality metrics (blur, brightness, contrast) exhibit temporal drift or abrupt degradation?

- **Anomaly isolation**  
  Can isolated failures be distinguished from long-term drift or seasonal effects using multi-modal context?

---

## 3. ETL Pipeline Overview

The ETL process is implemented as a **multi-branch, log-driven pipeline**. Sensor logs define the authoritative event timeline, while image and audio data are processed independently to enable non-circular validation.

### 3.1 Log-Driven Event Extraction (Foundation Layer)

**Input**
- Newline-delimited JSON traffic logs (`traffic.txt*`)

**Process**
- Parse timestamps, file paths, and sensor configuration
- Extract sensor-reported audio measurements (`snd_lvl`, rolling `dba[]`)
- Normalize timestamps and calendar dates

**Output**
- Structured CSVs indexing sensor events and referenced files

---

### 3.2 Audio Waveform Quality Extraction (Signal Branch)

**Input**
- Raw `.mp3` audio files

**Process**
- Offline waveform decoding
- RMS amplitude, zero-crossing rate (ZCR), duration, file size
- Daily aggregation aligned to event dates

**Output**
- `audio_quality.csv`
- `audio_quality_daily.csv`

---

### 3.3 Audio Sensor Aggregation (Sensor Branch)

**Input**
- Parsed traffic logs

**Process**
- Aggregate rolling dBA windows
- Compute daily summary statistics

**Output**
- `audio_sensor_daily.csv`

---

### 3.4 Image Quality Extraction (Vision Branch)

**Input**
- Raw traffic images

**Process**
- Compute blur (Laplacian variance), brightness, contrast, file size
- File-level persistence and daily aggregation
- Outlier clipping

**Output**
- `image_quality.csv`
- `image_quality_daily.csv`
- `image_quality_daily_clipped.csv`

---

### 3.5 Cross-Modal Integration

**Process**
- Date-based joins across modalities
- Normalization and alignment
- Persistence and imbalance metrics

**Purpose**
Enable cross-modal interpretation of anomalies as:
- Capture failures
- Modality-specific degradation
- System-level issues

---

## 4. Analysis Approach

The analysis is structured around **three complementary perspectives**:
1. Sensor–signal consistency
2. Cross-modal data availability
3. Image quality stability

---

## 5. Visualizations and Interpretation

All figures are generated via scripts and saved as **PNG (static)** and **HTML (interactive)**.

### 5.1 Image and Audio Availability Heatmaps

These calendar heatmaps visualize daily file availability across modalities.

**Images**
- `figures/2025_images_heatmap.png`
- `figures/2025_audio_heatmap.png`
- `figures/2025_contrast_heatmap.png`

```text
Image files per day, Audio files per day, and modality imbalance

### Interpretation

Under normal operation, image and audio capture volumes exhibit similar temporal structure. Isolated days with strong imbalance—high image counts paired with minimal audio or vice versa—indicate **modality-specific capture or persistence failures**, rather than environmental variation.

---

## 5.2 Image Quality Calendar Heatmaps

These figures evaluate the **temporal stability of image quality**.

**Images**
- `figures/2025_blur_heatmap.png`
- `figures/2025_brightness_heatmap.png`
- `figures/2025_contrast_heatmap.png`

### Interpretation

Image quality metrics remain largely stable across the observation period. Abrupt, localized shifts suggest **temporary obstruction or configuration changes**, rather than gradual camera degradation.

---

## 5.3 Sensor Sound Level vs Audio Capture Volume

This scatter plot compares **sensor-reported loudness** to **audio persistence**.

**Image**
- `figures/image_vs_audio_count_scatter.png`

### Interpretation

Most days show coherent behavior. Isolated outliers with **high sensor loudness but near-zero audio persistence** strongly indicate **audio capture failure**, not low ambient sound.

---

## 5.4 Sensor vs Waveform Amplitude (Time Series)

This figure compares **normalized sensor-reported sound levels** and **waveform-derived RMS amplitude**.

**Image**
- `figures/sensor_vs_waveform_amplitude_time_series.png`

### Interpretation

Temporal coherence dominates, with divergence limited to isolated days. These deviations align with **persistence failures**, rather than systematic drift or seasonal effects.

---

## 6. Repository Structure

```text
ia626_project/
├── scripts/      # ETL and figure-generation scripts
├── results/      # Generated CSV outputs
├── figures/      # PNG and HTML visualizations
├── notebooks/    # Exploratory notebooks
└── README.md

## 7. Reproducibility

- All transformations are script-driven  
- Raw data are omitted due to size constraints  
- Directory structure and data schemas are fully documented  
- Each ETL branch can be rerun independently  
- All figures are reproducible from versioned CSV outputs  

---

## 8. Code / API Appendix

- Python 3.10  
- pandas  
- numpy  
- librosa  
- plotly  
- matplotlib  
- pathlib  

All dependencies are open-source. No proprietary APIs or external services are required.

---

## 9. Conclusion

This project demonstrates how **multi-modal sensor systems** can be rigorously validated using a **log-driven, cross-modal ETL design**. By independently deriving signal- and image-based metrics and aligning them with sensor metadata, the analysis avoids circular validation and enables robust anomaly detection.

The results show that:
- Normal operation exhibits stable cross-modal relationships  
- Anomalies are rare, isolated, and modality-specific  
- Image quality remains stable over long periods  
- Cross-modal reasoning is essential for correct interpretation  

Overall, the project illustrates how careful pipeline design and targeted visualization can transform heterogeneous sensor data into interpretable evidence of system performance and reliability.