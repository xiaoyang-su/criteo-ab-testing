# Data Card: Criteo Uplift Modeling Dataset (v2.1)

## 1. Source and version

| Item | Details |
| --- | --- |
| Dataset | **CRITEO-UPLIFTv2.1** (corrected release) |
| Creator | Criteo AI Lab |
| Official host | [criteo/criteo-uplift on Hugging Face](https://huggingface.co/datasets/criteo/criteo-uplift) |
| Original publisher | [Criteo AI Lab dataset page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) |
| Archive | `criteo-research-uplift-v2.1.csv.gz` |
| Format | Gzip-compressed CSV |
| Observations | **13,979,592** (one row per user in the released benchmark) |
| Columns | **16**: 12 anonymized features and 4 binary variables |
| Reported treatment share | Approximately **85%** (rounded by Criteo) |
| Data license | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |

**Version warning.** The original v1 release (approximately 25 million rows) was deprecated after Criteo identified a leakage/confounding issue: treatment allocation differed across advertiser experiments, and feature distributions could partly reveal advertiser identity. The corrected v2 release rebalanced the treatment allocation; this project uses the official **v2.1** archive only. Older descriptions on Criteo's website may still refer to v1.

## 2. Experimental context and schema

The dataset combines several randomized advertising incrementality tests. Users were randomly assigned to an advertising-eligible treatment group or to a holdout control group. Outcomes were recorded over a two-week observation window.

| Column(s) | Meaning | Analytical role |
| --- | --- | --- |
| `f0`–`f11` | Anonymized, pre-assignment user characteristics | Covariates |
| `treatment` | Randomized assignment: 1 = eligible for advertising, 0 = holdout | **Primary treatment variable (ITT)** |
| `exposure` | Whether an advertisement was actually shown | **Post-assignment variable**, not randomized treatment |
| `visit` | Whether the user visited the advertiser's website | Primary outcome in this portfolio |
| `conversion` | Whether the user converted | Secondary, rare-event outcome |

**Feature types:** Although the public CSV stores all 12 features as numeric values, only `f0`, `f2`, `f7`, and `f10` are continuous. The remaining eight (`f1`, `f3`, `f4`, `f5`, `f6`, `f8`, `f9`, `f11`) are encoded categorical variables with many distinct levels. Their numeric codes must not be interpreted as ordered measurements.

## 3. Known limitations and implications

1. **Anonymized features:** Feature names and real-world meanings are unavailable, limiting interpretable customer segmentation and business narratives.
2. **Non-uniform negative-label sampling:** Criteo deliberately sampled negative outcomes non-uniformly. Observed rates and treatment effects in the released benchmark must not be presented as the original advertiser population's campaign incrementality.
3. **Multiple experiments pooled:** Records come from several advertiser tests, but advertiser/test identifiers are not provided. Experiment-level heterogeneity, clustering, and per-advertiser effects cannot be audited directly.
4. **No stable user or experiment ID:** Unique-user deduplication, individual-level longitudinal linkage, and experiment-level grouping cannot be validated from the public columns. Exact duplicate rows do not necessarily represent duplicate users.
5. **No timestamps:** Pre-period trends, seasonality, time-based splits, and sequential monitoring cannot be reconstructed. The two-week outcome window is documented, but row-level event times are absent.
6. **No advertising cost or revenue:** Observed ROI, profit, and monetary lift cannot be calculated. Any business-case analysis must use explicitly labeled hypothetical cost/value assumptions and sensitivity ranges.
7. **Encoded categorical features:** Treat the eight categorical features as categories, not continuous numbers; numerical-code means, distances, and continuous-feature balance statistics can be misleading.
8. **Assignment differs from exposure:** `exposure` occurs after random assignment and is endogenous. A comparison of exposed versus unexposed users does not by itself identify a causal effect. The main analysis uses `treatment` for intent-to-treat (ITT) estimation.
9. **Incomplete randomization metadata:** Criteo reports the treatment allocation as approximately 85%, not an exact design probability. A formal sample-ratio-mismatch test against precisely 0.850000 would be assumption-dependent.
10. **No predefined train/test split:** Any machine-learning evaluation split is created and documented by this project, not supplied as a distinct randomized trial or external validation dataset.

**Scope of claims:** This repository is a *retrospective analysis* of a released RCT benchmark, not an experiment conducted or deployed by the repository author. Results apply to the released, processed sample; external validity to live advertising campaigns is limited.

## 4. License and data distribution policy

The official Criteo Hugging Face repository currently identifies the data license as **Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. Attribution is required; commercial use is restricted; sharing adapted dataset material may trigger ShareAlike obligations. See the [full license](https://creativecommons.org/licenses/by-nc-sa/4.0/).

**Repository policy:** This project does **not** commit or redistribute raw, extracted, or processed row-level datasets (including Parquet copies). It commits only documentation, download/processing code, checksums, analytical code, and non-row-level results. Users must download the data from Criteo and follow the original license. A separate license for this repository's code does not override the dataset license.

*Licensing note:* The 2021 paper's datasheet appendix contains a different CC BY-SA 4.0 description. For this portfolio, follow the more restrictive license currently displayed by Criteo's official hosting page; obtain clarification from Criteo before relying on a different interpretation.

## 5. Download and integrity verification

Official download URL:

`https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz`

Download locally (for example, with `curl`):

```bash
mkdir -p data/raw
curl -L --fail --retry 3 \
  -o data/raw/criteo-research-uplift-v2.1.csv.gz \
  https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz
```

Official Hugging Face archive **SHA-256** (for the compressed `.csv.gz` file, not extracted CSV or transformed Parquet):

```text
2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc
```

Verify on Windows PowerShell:

```powershell
(Get-FileHash data/raw/criteo-research-uplift-v2.1.csv.gz -Algorithm SHA256).Hash.ToLower()
```

Compare the resulting hash with the published value above. Also validate the **13,979,592** row count and 16-column schema after ingestion. Keep downloaded and generated row-level files out of version control (e.g., using `.gitignore`).

## 6. Academic citations

Please cite both the original release and the later corrected-dataset benchmark:

1. Diemert, E., Betlei, A., Renaudin, C., & Amini, M.-R. (2018). *A Large Scale Benchmark for Uplift Modeling*. AdKDD and TargetAd Workshop, KDD 2018. [Paper](https://www.adkdd.org/papers/a-large-scale-benchmark-for-uplift-modeling/2018).
2. Diemert, E., Betlei, A., Renaudin, C., Amini, M.-R., Gregoir, T., & Rahier, T. (2021). *A Large Scale Benchmark for Individual Treatment Effect Prediction and Uplift Modeling*. arXiv:2111.10106. [Paper](https://arxiv.org/abs/2111.10106).

Additional official references: [Criteo dataset page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) · [Hugging Face dataset repository](https://huggingface.co/datasets/criteo/criteo-uplift) · [Official benchmark code](https://github.com/criteo-research/large-scale-ITE-UM-benchmark).