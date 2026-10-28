# Vietnam Community Health Screening: BMI–Blood Pressure Analysis

Reproducible statistical analysis for the cross-sectional association between body mass index (BMI) and systolic blood pressure among de-identified health-screening encounters from adults aged 18–59 years in 2026.

## Repository contents

- `M3_BMI_HuyetAp_Final_Analysis.ipynb`: executed analysis notebook.
- `build_m3_final_notebook.py`: reproducibly builds the notebook.
- `figures/`: 12 publication-ready figures (17 visual panels).
- `tables/`: aggregate results only: descriptive statistics, quality audit, hypothesis tests, regression, and sensitivity analysis.
- `requirements.txt`: Python dependencies.

## Data access

Individual-level records are **not included** in this repository. The notebook expects the de-identified CSV at the local path configured in the notebook. Dataset access is managed separately through the gated Hugging Face repository:

<https://huggingface.co/datasets/SpringWang08/vietnam-community-health-screening-bmi-blood-pressure-2026>

## Analysis scope

The analysis includes data-quality checks, exploratory visualizations, Welch t-test, one-way ANOVA, Chi-square, Pearson/Spearman correlation, multivariable ordinary least squares regression, diagnostics, and sensitivity analysis for repeated-source-record flags.

The primary model is:

`Systolic blood pressure ~ BMI + age + sex + pulse`

## Interpretation boundary

This is a cross-sectional health-screening analysis. Results describe statistical associations in the released analytical cohort only. They do not establish causality, clinical diagnosis, treatment recommendations, or national representativeness.

## Privacy

No source workbook, direct identifiers, or individual-level CSV file is included here. Aggregate tables and figures remain subject to the project’s data-governance conditions.

## Related literature

- Nguyen Minh Q, Nguyen Vo M. *Anthropometric Indexes for Predicting High Blood Pressure in Vietnamese Adults: A Cross-Sectional Study.* Integr Blood Press Control. 2020;13:181–186. doi:10.2147/IBPC.S281996.
- Wang J, et al. *The importance of waist circumference and body mass index in cross-sectional relationships with risk of cardiovascular disease in Vietnam.* PLoS One. 2018. PMID:29813112.
- Nguyen Duc N, et al. *Impact of body mass index and waist circumference on blood pressure: A cross-sectional survey in a population living in the Vietnam northern mountainous.* Diabetes Metab Syndr. 2019;13(2):1399–1404. doi:10.1016/j.dsx.2019.02.015.
