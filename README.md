# Vietnam Community Health Screening: BMI and Blood Pressure Analysis

Reproducible statistical analysis of the cross-sectional association between body mass index (BMI) and systolic blood pressure (SBP) in de-identified community periodic health-screening encounters among adults aged 18–59 years in 2026.

## Research question and interpretation boundary

**Research question:** In the cleaned analytical cohort, is BMI associated with SBP after accounting for age, sex, and pulse?

The primary model is:

`SBP ~ BMI + age + sex + pulse`

This is an encounter-level cross-sectional analysis. Results describe statistical associations in this analytical cohort only; they do **not** establish causality, provide a clinical diagnosis or treatment recommendation, or claim national representativeness.

## Release contents

- `M3_BMI_HuyetAp_Final_Analysis.ipynb`: executed notebook with a portable input-data path and local paths removed from displayed output.
- `build_m3_final_notebook.py`: reproducibly builds the analysis notebook.
- `figures/`: 17 question-driven PNG figures, including distribution, diagnostic, subgroup, regression, sensitivity, and cross-validation views.
- `tables/`: 24 aggregate-only result tables. They cover data quality, distributions, assumptions, robust tests, correlation, adjusted regression, model comparison, cross-validation, and sensitivity analysis.
- `reports/`: Vietnamese rubric report and English research-paper-style report, in DOCX and PDF.
- `scripts/`: notebook-presentation, advanced-validation, report-build, and public-release-sanitizer scripts.
- `requirements.txt`: Python dependencies for reproducing the notebook.

## Reproduce safely

Individual-level data are intentionally absent. After access is granted to the de-identified CSV, either place it at `data/Research_Data.csv` or set `M3_DATA_PATH` to its local file path. Never use the identified source workbook.

```bash
python -m pip install -r requirements.txt
export M3_DATA_PATH="/secure/location/Research_Data.csv"
jupyter nbconvert --to notebook --execute --inplace M3_BMI_HuyetAp_Final_Analysis.ipynb \
  --ExecutePreprocessor.timeout=300
```

The de-identified dataset is governed separately through the gated Hugging Face repository: <https://huggingface.co/datasets/SpringWang08/vietnam-community-health-screening-bmi-blood-pressure-2026>.

## Data governance

No source workbook, direct identifiers, individual-level CSV, or record-level export is committed to this repository. Published figures and CSV tables are aggregate analytical outputs only. Access to the de-identified microdata remains subject to the dataset's gated-access conditions.

## Analytical highlights

- Data-quality flow, missingness/duplicate checks, and IQR outlier audit.
- Distribution diagnostics for BMI and SBP: histogram/KDE, Q–Q plot, skewness, kurtosis, and normality checks.
- Welch t-test, classical one-way ANOVA, Welch ANOVA with Holm-corrected pairwise Welch tests, and chi-square with expected-count audit.
- Pearson/Spearman correlation and an adjusted OLS model with VIF and residual diagnostics.
- HC3 robust confidence intervals, Breusch–Pagan and Cook's distance diagnostics.
- Nested model comparison, 5-fold cross-validation, and multiple sensitivity analyses.

## Context literature

- Nguyen Minh Q, Nguyen Vo M. *Anthropometric Indexes for Predicting High Blood Pressure in Vietnamese Adults: A Cross-Sectional Study.* Integr Blood Press Control. 2020;13:181–186. doi:10.2147/IBPC.S281996.
- Wang J, et al. *The importance of waist circumference and body mass index in cross-sectional relationships with risk of cardiovascular disease in Vietnam.* PLoS One. 2018. PMID:29813112.
- Nguyen Duc N, et al. *Impact of body mass index and waist circumference on blood pressure: A cross-sectional survey in a population living in the Vietnam northern mountainous.* Diabetes Metab Syndr. 2019;13(2):1399–1404. doi:10.1016/j.dsx.2019.02.015.
