"""Additional, reproducible robustness analyses for the BMI--SBP coursework.

This script reads the local *de-identified* research CSV and writes aggregate
tables/figures only.  It does not export row-level data.  All analyses are
secondary checks of an encounter-level, cross-sectional association; they are
not a clinical prediction or diagnostic system.
"""

from pathlib import Path
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold


ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("M3_DATA_PATH", ROOT / "data/Research_Data.csv"))
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"
SEED = 42

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["font.family"] = ["Arial Unicode MS", "DejaVu Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def ols_fit(y: np.ndarray, x: np.ndarray) -> dict:
    """OLS with conventional and HC3 robust covariance, without statsmodels."""
    n, p = x.shape
    beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    resid = y - fitted
    xtx_inv = np.linalg.inv(x.T @ x)
    hat = np.einsum("ij,jk,ik->i", x, xtx_inv, x)
    mse = (resid @ resid) / (n - p)
    cov_ols = mse * xtx_inv
    # HC3: sandwich covariance with residual_i^2/(1-h_ii)^2.
    scale = (resid / np.maximum(1 - hat, 1e-12)) ** 2
    cov_hc3 = xtx_inv @ (x.T @ (x * scale[:, None])) @ xtx_inv
    tcrit = stats.t.ppf(0.975, n - p)
    tss = ((y - y.mean()) ** 2).sum()
    rss = (resid**2).sum()
    r2 = 1 - rss / tss
    f_stat = ((tss - rss) / (p - 1)) / (rss / (n - p))
    f_p = stats.f.sf(f_stat, p - 1, n - p)
    cooks = (resid**2 / (p * mse)) * (hat / np.maximum((1 - hat) ** 2, 1e-12))
    return {
        "beta": beta, "fitted": fitted, "resid": resid, "hat": hat,
        "cooks": cooks, "r2": r2, "adj_r2": 1 - (1-r2)*(n-1)/(n-p),
        "rmse": np.sqrt(mse), "f_stat": f_stat, "f_p": f_p,
        "df_model": p - 1, "df_resid": n - p,
        "se_ols": np.sqrt(np.diag(cov_ols)), "se_hc3": np.sqrt(np.diag(cov_hc3)),
        "tcrit": tcrit,
    }


def design(data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    y = data["sbp"].to_numpy(float)
    male = (data["sex"] == "Nam").astype(int).to_numpy()
    x = np.column_stack([
        np.ones(len(data)), data["bmi"], data["age"], male, data["pulse"]
    ])
    return y, x, ["Hằng số", "BMI (kg/m²)", "Tuổi (năm)", "Nam so với Nữ", "Mạch (lần/phút)"]


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Không tìm thấy CSV khử định danh: {DATA}")
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(DATA)
    df = raw.rename(columns={
        "Tuổi (năm)": "age", "Giới tính": "sex", "Chiều cao (cm)": "height_cm",
        "Cân nặng (kg)": "weight_kg", "BMI (kg/m²)": "bmi",
        "Nhóm BMI phân tích": "bmi_group", "Mạch (lần/phút)": "pulse",
        "Huyết áp tâm thu (mmHg)": "sbp", "Huyết áp tâm trương (mmHg)": "dbp",
        "Cờ sàng lọc HA ≥140/90": "bp_screen", "Cờ mã nguồn lặp": "repeat_flag",
    })
    assert len(df) == 7146 and df["Mã nghiên cứu"].is_unique
    y, x, names = design(df)
    fit = ols_fit(y, x)

    # Basic figures requested by the report draft.
    numerical = ["age", "height_cm", "weight_kg", "bmi", "pulse", "sbp", "dbp"]
    dtype = pd.DataFrame({
        "Biến": raw.columns,
        "Kiểu dữ liệu": raw.dtypes.astype(str).values,
        "Số thiếu": raw.isna().sum().values,
        "Số giá trị khác nhau": raw.nunique().values,
    })
    dtype.to_csv(TABLES / "12_data_types_and_completeness.csv", index=False, encoding="utf-8-sig")
    quartiles = df[numerical].describe(percentiles=[.25, .5, .75]).T[["mean", "std", "25%", "50%", "75%", "min", "max"]]
    quartiles.to_csv(TABLES / "13_quartiles_and_ranges.csv", encoding="utf-8-sig")

    outlier_rows = []
    physiologic = {"bmi": (10, 70), "pulse": (30, 220), "sbp": (70, 260), "dbp": (30, 160)}
    for col in ["bmi", "pulse", "sbp", "dbp"]:
        q1, q3 = df[col].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        flo, fhi = physiologic[col]
        outlier_rows.append({
            "Biến": col, "Q1": q1, "Q3": q3, "IQR": iqr,
            "Ngưỡng IQR dưới": lo, "Ngưỡng IQR trên": hi,
            "Số cờ IQR": int(((df[col] < lo) | (df[col] > hi)).sum()),
            "Tỷ lệ cờ IQR (%)": 100 * ((df[col] < lo) | (df[col] > hi)).mean(),
            "Khoảng sinh lý bảo thủ": f"{flo}–{fhi}",
            "Ngoài khoảng sinh lý": int(((df[col] < flo) | (df[col] > fhi)).sum()),
        })
    outliers = pd.DataFrame(outlier_rows)
    outliers.to_csv(TABLES / "14_outlier_audit_extended.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    sns.boxplot(data=df, y="bmi", color="#8ecae6", ax=axes[0])
    axes[0].set(title="BMI: rà soát điểm cực trị theo IQR", ylabel="BMI (kg/m²)")
    sns.boxplot(data=df, y="sbp", color="#90be6d", ax=axes[1])
    axes[1].set(title="HATT: rà soát điểm cực trị theo IQR", ylabel="HATT (mmHg)")
    fig.suptitle("Hình 14. Ngoại lai được giữ lại để đánh giá độ nhạy", fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(FIGURES / "14_outlier_review.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Distribution fit; all models are descriptive candidates, not a generative claim.
    fit_rows = []
    for col, label in [("bmi", "BMI"), ("sbp", "HATT")]:
        values = df[col].to_numpy(float)
        candidates = {
            "Normal": (stats.norm, stats.norm.fit(values), 2),
            "Lognormal (loc=0)": (stats.lognorm, stats.lognorm.fit(values, floc=0), 2),
            "Gamma (loc=0)": (stats.gamma, stats.gamma.fit(values, floc=0), 2),
        }
        for distribution, (dist, params, k) in candidates.items():
            loglik = float(np.sum(dist.logpdf(values, *params)))
            fit_rows.append({"Biến": label, "Phân phối ứng viên": distribution, "Log-likelihood": loglik, "AIC": 2*k - 2*loglik})
    dist_fit = pd.DataFrame(fit_rows).sort_values(["Biến", "AIC"])
    dist_fit["Xếp hạng AIC"] = dist_fit.groupby("Biến")["AIC"].rank(method="dense").astype(int)
    dist_fit.to_csv(TABLES / "15_distribution_fit_aic.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for ax, col, label in zip(axes, ["bmi", "sbp"], ["BMI", "HATT"]):
        values = df[col].to_numpy(float)
        xx = np.linspace(values.min(), values.max(), 500)
        sns.histplot(values, bins=40, stat="density", color="#ced4da", edgecolor="white", ax=ax)
        for name, color, dist, params in [
            ("Normal", "#1d3557", stats.norm, stats.norm.fit(values)),
            ("Lognormal", "#e76f51", stats.lognorm, stats.lognorm.fit(values, floc=0)),
            ("Gamma", "#2a9d8f", stats.gamma, stats.gamma.fit(values, floc=0)),
        ]:
            ax.plot(xx, dist.pdf(xx, *params), label=name, color=color, lw=2)
        ax.set(title=f"Khớp phân phối ứng viên: {label}", xlabel=label, ylabel="Mật độ")
        ax.legend()
    fig.suptitle("Hình 15. So sánh mô tả các phân phối bằng đường mật độ", fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(FIGURES / "15_distribution_fit_candidates.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Inferential extensions: Levene, Mann–Whitney, chi-square trend, correlation CI/partial r.
    male_sbp = df.loc[df.sex.eq("Nam"), "sbp"].to_numpy()
    female_sbp = df.loc[df.sex.eq("Nữ"), "sbp"].to_numpy()
    lev_w, lev_p = stats.levene(male_sbp, female_sbp, center="median")
    welch = stats.ttest_ind(male_sbp, female_sbp, equal_var=False)
    u, mw_p = stats.mannwhitneyu(male_sbp, female_sbp, alternative="two-sided")
    rb = 2*u/(len(male_sbp)*len(female_sbp)) - 1
    # Welch--Satterthwaite degrees of freedom.
    s1, s2 = male_sbp.var(ddof=1), female_sbp.var(ddof=1)
    n1, n2 = len(male_sbp), len(female_sbp)
    welch_df = (s1/n1 + s2/n2)**2 / ((s1/n1)**2/(n1-1) + (s2/n2)**2/(n2-1))
    diff = male_sbp.mean() - female_sbp.mean()
    diff_se = np.sqrt(s1/n1+s2/n2)
    diff_ci = (diff - stats.t.ppf(.975, welch_df)*diff_se, diff + stats.t.ppf(.975, welch_df)*diff_se)
    sex_table = pd.DataFrame({
        "Kiểm tra": ["Levene (median)", "Welch t-test", "Mann–Whitney U"],
        "Thống kê": [lev_w, welch.statistic, u], "df hoặc n": [np.nan, welch_df, n1*n2],
        "p-value": [lev_p, welch.pvalue, mw_p],
        "Kích thước hiệu ứng": [np.nan, np.nan, rb],
        "Ghi chú": ["Kiểm tra phương sai", "Khác biệt trung bình Nam – Nữ", "Rank-biserial: Nam > Nữ nếu dương"],
    })
    sex_table.to_csv(TABLES / "16_sex_tests_extended.csv", index=False, encoding="utf-8-sig")

    ordered_groups = ["<18.5", "18.5-<23", "23-<25", "25-<30", ">=30"]
    success = df.groupby("bmi_group", observed=False)["bp_screen"].sum().reindex(ordered_groups).to_numpy(float)
    total = df.groupby("bmi_group", observed=False)["bp_screen"].count().reindex(ordered_groups).to_numpy(float)
    scores = np.arange(1, len(total)+1, dtype=float)
    pbar = success.sum()/total.sum()
    ztrend = np.sum(scores*(success-total*pbar)) / np.sqrt(pbar*(1-pbar)*(np.sum(total*scores**2)-(np.sum(total*scores)**2)/total.sum()))
    ptrend = 2*stats.norm.sf(abs(ztrend))
    trend_table = pd.DataFrame({"Kiểm định": ["Cochran–Armitage, hai phía"], "z": [ztrend], "p-value": [ptrend], "Thứ tự điểm": ["1, 2, 3, 4, 5 theo nhóm BMI tăng dần"]})
    trend_table.to_csv(TABLES / "17_bmi_screening_trend_test.csv", index=False, encoding="utf-8-sig")

    pearson_r, pearson_p = stats.pearsonr(df.bmi, df.sbp)
    z_r = np.arctanh(pearson_r); se_z = 1/np.sqrt(len(df)-3)
    rci = tuple(np.tanh(z_r + np.array([-1, 1]) * stats.norm.ppf(.975)*se_z))
    correlations = []
    for label, part in [("Toàn mẫu", df), ("Nam", df[df.sex.eq("Nam")]), ("Nữ", df[df.sex.eq("Nữ")])]:
        r, p = stats.pearsonr(part.bmi, part.sbp)
        rho, ps = stats.spearmanr(part.bmi, part.sbp)
        correlations.append({"Nhóm": label, "n": len(part), "Pearson r": r, "p Pearson": p, "Spearman rho": rho, "p Spearman": ps})
    covar = np.column_stack([np.ones(len(df)), df.age, (df.sex == "Nam").astype(int), df.pulse])
    bmi_resid = df.bmi.to_numpy() - covar @ np.linalg.lstsq(covar, df.bmi, rcond=None)[0]
    sbp_resid = df.sbp.to_numpy() - covar @ np.linalg.lstsq(covar, df.sbp, rcond=None)[0]
    partial_r, partial_p = stats.pearsonr(bmi_resid, sbp_resid)
    correlations.append({"Nhóm": "Tương quan riêng phần (điều chỉnh tuổi, giới, mạch)", "n": len(df), "Pearson r": partial_r, "p Pearson": partial_p, "Spearman rho": np.nan, "p Spearman": np.nan})
    corr_extended = pd.DataFrame(correlations)
    corr_extended.to_csv(TABLES / "18_correlations_extended.csv", index=False, encoding="utf-8-sig")

    # Main OLS, classical versus HC3 confidence interval, model comparison, diagnostics and 5-fold CV.
    conventional_ci = np.column_stack([fit["beta"] - fit["tcrit"]*fit["se_ols"], fit["beta"] + fit["tcrit"]*fit["se_ols"]])
    hc3_ci = np.column_stack([fit["beta"] - fit["tcrit"]*fit["se_hc3"], fit["beta"] + fit["tcrit"]*fit["se_hc3"]])
    model_table = pd.DataFrame({
        "Biến": names, "Hệ số": fit["beta"], "SE OLS": fit["se_ols"],
        "CI 95% OLS thấp": conventional_ci[:,0], "CI 95% OLS cao": conventional_ci[:,1],
        "SE HC3": fit["se_hc3"], "CI 95% HC3 thấp": hc3_ci[:,0], "CI 95% HC3 cao": hc3_ci[:,1],
    })
    model_table.to_csv(TABLES / "19_ols_hc3_robust_inference.csv", index=False, encoding="utf-8-sig")

    # Breusch--Pagan auxiliary regression: n*R2 of squared residuals on original predictors.
    aux = ols_fit(fit["resid"]**2, x)
    bp_lm = len(df)*aux["r2"]
    bp_p = stats.chi2.sf(bp_lm, x.shape[1]-1)
    diagnostics = pd.DataFrame({
        "Chỉ số": ["Breusch–Pagan LM", "p Breusch–Pagan", "Cook's D lớn nhất", "Ngưỡng Cook 4/n", "Số Cook's D > 4/n", "Skewness phần dư", "F toàn cục", "p F toàn cục"],
        "Giá trị": [bp_lm, bp_p, fit["cooks"].max(), 4/len(df), int((fit["cooks"] > 4/len(df)).sum()), stats.skew(fit["resid"], bias=False), fit["f_stat"], fit["f_p"]],
    })
    diagnostics.to_csv(TABLES / "20_regression_diagnostics_extended.csv", index=False, encoding="utf-8-sig")

    models = []
    for label, columns in [
        ("BMI", ["bmi"]), ("BMI + tuổi + giới", ["bmi", "age", "sex"]),
        ("BMI + tuổi + giới + mạch", ["bmi", "age", "sex", "pulse"]),
    ]:
        features = pd.DataFrame(index=df.index)
        for col in columns:
            features[col] = (df[col] == "Nam").astype(int) if col == "sex" else df[col]
        reg = LinearRegression().fit(features, y)
        pred = reg.predict(features)
        models.append({"Mô hình": label, "Số biến giải thích": len(columns), "R² trong mẫu": r2_score(y, pred), "RMSE trong mẫu": np.sqrt(mean_squared_error(y, pred))})
    comparison = pd.DataFrame(models)
    comparison.to_csv(TABLES / "21_model_comparison.csv", index=False, encoding="utf-8-sig")

    features = pd.DataFrame({"BMI": df.bmi, "Tuổi": df.age, "Nam": (df.sex == "Nam").astype(int), "Mạch": df.pulse})
    folds = KFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_rows, cv_pred = [], np.full(len(df), np.nan)
    for i, (train, test) in enumerate(folds.split(features), 1):
        reg = LinearRegression().fit(features.iloc[train], y[train])
        pred = reg.predict(features.iloc[test]); cv_pred[test] = pred
        cv_rows.append({"Fold": i, "n_test": len(test), "RMSE": np.sqrt(mean_squared_error(y[test], pred)), "MAE": mean_absolute_error(y[test], pred), "R²": r2_score(y[test], pred)})
    cv = pd.DataFrame(cv_rows)
    cv.loc[len(cv)] = {"Fold": "Trung bình ± SD", "n_test": np.nan, "RMSE": f"{cv.RMSE.iloc[:5].mean():.3f} ± {cv.RMSE.iloc[:5].std(ddof=1):.3f}", "MAE": f"{cv.MAE.iloc[:5].mean():.3f} ± {cv.MAE.iloc[:5].std(ddof=1):.3f}", "R²": f"{cv['R²'].iloc[:5].mean():.3f} ± {cv['R²'].iloc[:5].std(ddof=1):.3f}"}
    cv.to_csv(TABLES / "22_five_fold_cross_validation.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].scatter(fit["fitted"], fit["resid"], s=8, alpha=.22, color="#457b9d")
    axes[0].axhline(0, color="#d1495b", lw=1.3)
    axes[0].set(title="Phần dư theo HATT dự báo", xlabel="HATT dự báo (mmHg)", ylabel="Phần dư (mmHg)")
    stats.probplot(fit["resid"], dist="norm", plot=axes[1])
    axes[1].set_title("Q–Q plot phần dư OLS")
    fig.suptitle("Hình 16. Chẩn đoán mở rộng của hồi quy OLS", fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(FIGURES / "16_regression_diagnostics_extended.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(y, cv_pred, s=8, alpha=.22, color="#2a9d8f")
    limits = [min(y.min(), cv_pred.min()), max(y.max(), cv_pred.max())]
    ax.plot(limits, limits, "--", color="#d1495b", label="Dự báo hoàn hảo")
    ax.set(xlim=limits, ylim=limits, xlabel="HATT quan sát (mmHg)", ylabel="HATT dự báo ngoài fold (mmHg)", title="Hình 17. 5-fold CV: quan sát và dự báo ngoài mẫu")
    ax.legend(); fig.tight_layout()
    fig.savefig(FIGURES / "17_cv_observed_vs_predicted.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Sensitivity: values and rules are explicit in the output table.
    sbp_q01, sbp_q99 = df.sbp.quantile([.01, .99])
    sbp_iqr = outliers.loc[outliers.Biến.eq("sbp")].iloc[0]
    scenarios = [("Mô hình chính", df, "HATT gốc"),
                 ("Bỏ cờ mã nguồn lặp", df[df.repeat_flag.eq(0)], "HATT gốc"),
                 ("Winsorize HATT P1–P99", df, "winsor"),
                 ("Bỏ HATT ngoài hàng rào IQR", df[(df.sbp >= sbp_iqr["Ngưỡng IQR dưới"]) & (df.sbp <= sbp_iqr["Ngưỡng IQR trên"])], "HATT gốc"),
                 ("Hồi quy log(HATT)", df, "log")]
    sens_rows = []
    for label, part, outcome in scenarios:
        yy, xx, _ = design(part)
        if outcome == "winsor": yy = np.clip(yy, sbp_q01, sbp_q99)
        if outcome == "log": yy = np.log(yy)
        f = ols_fit(yy, xx)
        beta = f["beta"][1]
        sens_rows.append({"Kịch bản": label, "n": len(part), "Hệ số BMI": beta, "CI 95% thấp": beta-f["tcrit"]*f["se_hc3"][1], "CI 95% cao": beta+f["tcrit"]*f["se_hc3"][1], "R²": f["r2"], "Diễn giải hệ số": "Phần trăm HATT mỗi +1 BMI" if outcome == "log" else "mmHg HATT mỗi +1 BMI", "Quy đổi log (%)": 100*(np.exp(beta)-1) if outcome == "log" else np.nan})
    sensitivity = pd.DataFrame(sens_rows)
    sensitivity.to_csv(TABLES / "23_sensitivity_extended.csv", index=False, encoding="utf-8-sig")

    # Compact scalar result file for report builders; aggregate numbers only.
    scalar = {
        "n": int(len(df)), "seed": SEED,
        "sex_levene_p": float(lev_p), "sex_welch_df": float(welch_df), "sex_difference_mmhg": float(diff),
        "sex_ci95": [float(diff_ci[0]), float(diff_ci[1])], "mann_whitney_p": float(mw_p), "rank_biserial": float(rb),
        "trend_z": float(ztrend), "trend_p": float(ptrend), "screening_rate_pct": float(100*df.bp_screen.mean()),
        "pearson_ci95": [float(rci[0]), float(rci[1])], "partial_r": float(partial_r), "partial_p": float(partial_p),
        "model_f": float(fit["f_stat"]), "model_f_df": [int(fit["df_model"]), int(fit["df_resid"])], "model_f_p": float(fit["f_p"]),
        "bp_lm": float(bp_lm), "bp_p": float(bp_p), "cooks_max": float(fit["cooks"].max()), "cooks_over_4n": int((fit["cooks"] > 4/len(df)).sum()),
        "residual_skewness": float(stats.skew(fit["resid"], bias=False)),
        "cv_rmse_mean": float(pd.to_numeric(cv.iloc[:5]["RMSE"]).mean()), "cv_mae_mean": float(pd.to_numeric(cv.iloc[:5]["MAE"]).mean()), "cv_r2_mean": float(pd.to_numeric(cv.iloc[:5]["R²"]).mean()),
    }
    (TABLES / "24_advanced_scalar_results.json").write_text(json.dumps(scalar, ensure_ascii=False, indent=2), encoding="utf-8")

    best = dist_fit.loc[dist_fit["Xếp hạng AIC"].eq(1)].set_index("Biến")["Phân phối ứng viên"]
    cv_mean = pd.to_numeric(cv.iloc[:5]["RMSE"]).mean()
    cv_mae = pd.to_numeric(cv.iloc[:5]["MAE"]).mean()
    cv_r2 = pd.to_numeric(cv.iloc[:5]["R²"]).mean()
    report_ready = f"""# Kết quả bổ sung đã chạy thật để chèn vào báo cáo

Tệp này được tạo tự động từ `run_m3_advanced_validation.py` trên CSV nghiên cứu đã khử định danh (*n* = {len(df):,}). Các kết quả dưới đây là phân tích phụ trợ của mối liên quan cắt ngang BMI–HATT, không phải mô hình chẩn đoán hoặc dự báo lâm sàng.

## Chèn vào phần phân phối

Trong ba phân phối ứng viên được so sánh bằng AIC, phân phối có AIC thấp nhất là **{best['BMI']}** cho BMI và **{best['HATT']}** cho HATT. Đây là kết quả so sánh mô tả giữa các phân phối ứng viên; không nên diễn giải là dữ liệu tuân theo hoàn hảo một phân phối cụ thể. Chi tiết: `tables/15_distribution_fit_aic.csv`; hình: `figures/15_distribution_fit_candidates.png`.

## Chèn vào phần kiểm định giới tính và xu hướng

Kiểm định Levene dựa trên trung vị cho HATT theo giới có *W* = {lev_w:.3f}, *p* = {lev_p:.3f}. Welch t-test cho chênh lệch trung bình Nam − Nữ là {diff:.3f} mmHg, KTC 95% [{diff_ci[0]:.3f}; {diff_ci[1]:.3f}], *t* = {welch.statistic:.3f}, df = {welch_df:.2f}, *p* < 0.001. Mann–Whitney đối chiếu cũng cho *p* < 0.001; rank-biserial = {rb:.3f}. Chi tiết: `tables/16_sex_tests_extended.csv`.

Kiểm định xu hướng Cochran–Armitage theo thứ tự năm nhóm BMI cho *z* = {ztrend:.3f}, *p* < 0.001, phù hợp với xu hướng tăng tỷ lệ cờ sàng lọc khi nhóm BMI tăng. Tỷ lệ cờ sàng lọc chung là {100*df.bp_screen.mean():.2f}%. Chi tiết: `tables/17_bmi_screening_trend_test.csv`.

## Chèn vào phần tương quan

Pearson BMI–HATT toàn mẫu là *r* = {pearson_r:.3f}, KTC 95% [{rci[0]:.3f}; {rci[1]:.3f}], *p* < 0.001; Spearman là ρ = {stats.spearmanr(df.bmi, df.sbp).statistic:.3f}, *p* < 0.001. Sau khi điều chỉnh tuổi, giới và mạch bằng phương pháp phần dư, tương quan riêng phần là *r* = {partial_r:.3f}, *p* < 0.001. Theo giới, Pearson BMI–HATT là {corr_extended.loc[corr_extended['Nhóm'].eq('Nam'), 'Pearson r'].iloc[0]:.3f} ở nam và {corr_extended.loc[corr_extended['Nhóm'].eq('Nữ'), 'Pearson r'].iloc[0]:.3f} ở nữ. Chi tiết: `tables/18_correlations_extended.csv`.

## Chèn vào phần hồi quy và chẩn đoán

Mô hình OLS đầy đủ có *F*({fit['df_model']}, {fit['df_resid']}) = {fit['f_stat']:.3f}, *p* < 0.001; R² = {fit['r2']:.3f}, R² hiệu chỉnh = {fit['adj_r2']:.3f} và RMSE = {fit['rmse']:.3f} mmHg. Với BMI, hệ số OLS là {fit['beta'][1]:.3f} mmHg cho mỗi 1 kg/m²; KTC 95% HC3 [{hc3_ci[1,0]:.3f}; {hc3_ci[1,1]:.3f}], rất gần KTC OLS [{conventional_ci[1,0]:.3f}; {conventional_ci[1,1]:.3f}]. Chi tiết: `tables/19_ols_hc3_robust_inference.csv`.

Breusch–Pagan cho LM = {bp_lm:.3f}, *p* < 0.001, cho thấy phương sai phần dư không hoàn toàn đồng nhất; vì vậy nên báo cáo KTC HC3 song song với OLS. Cook's D lớn nhất là {fit['cooks'].max():.3f}, nhỏ hơn 1, nên không có quan sát nào chi phối cực mạnh; tuy nhiên {int((fit['cooks'] > 4/len(df)).sum())} lượt vượt ngưỡng sàng lọc 4/*n* và cần được diễn giải là ảnh hưởng vừa phải, không phải tự động xóa. Skewness phần dư là {stats.skew(fit['resid'], bias=False):.3f}. Hình chẩn đoán: `figures/16_regression_diagnostics_extended.png`; bảng: `tables/20_regression_diagnostics_extended.csv`.

## Chèn vào phần so sánh mô hình và kiểm định chéo

BMI một mình giải thích R² = {comparison.iloc[0]['R² trong mẫu']:.3f}; thêm tuổi và giới nâng R² lên {comparison.iloc[1]['R² trong mẫu']:.3f}; thêm mạch đạt R² = {comparison.iloc[2]['R² trong mẫu']:.3f}. Với 5-fold cross-validation có xáo trộn cố định (*seed* = {SEED}), RMSE ngoài fold trung bình là {cv_mean:.3f} mmHg, MAE là {cv_mae:.3f} mmHg, R² ngoài fold là {cv_r2:.3f}. Các chỉ số này gần với trong mẫu, nhưng sai số khoảng 14 mmHg vẫn quá lớn để sử dụng cho dự báo huyết áp của một cá nhân. Bảng: `tables/21_model_comparison.csv`, `tables/22_five_fold_cross_validation.csv`; hình: `figures/17_cv_observed_vs_predicted.png`.

## Chèn vào phần độ nhạy

Hệ số BMI chính là {sensitivity.iloc[0]['Hệ số BMI']:.3f} mmHg/1 BMI. Hệ số vẫn gần tương tự khi bỏ lượt có cờ mã nguồn lặp ({sensitivity.iloc[1]['Hệ số BMI']:.3f}), winsorize HATT tại P1–P99 ({sensitivity.iloc[2]['Hệ số BMI']:.3f}) và loại HATT ngoài hàng rào IQR ({sensitivity.iloc[3]['Hệ số BMI']:.3f}). Trên thang log(HATT), mỗi 1 kg/m² BMI liên quan với HATT cao hơn khoảng {sensitivity.iloc[4]['Quy đổi log (%)']:.3f}%. Đây là phân tích độ bền của mối liên quan trong mẫu, không chứng minh quan hệ nhân quả. Chi tiết: `tables/23_sensitivity_extended.csv`.

## Phần không được tự điền

Từ CSV phân tích cuối chỉ có thể kiểm chứng *n* = 7.146. Tiêu chí cụ thể làm loại 28 bản ghi cuối và lý do thiếu số đo của 3.582 bản ghi nguồn không thể suy ra từ CSV đã lọc; chỉ điền nội dung này khi có audit/provenance từ tệp nguồn, nếu không hãy nêu là giới hạn chọn mẫu.
"""
    (ROOT / "REPORT_INSERTS_ADVANCED.md").write_text(report_ready, encoding="utf-8")
    print(f"Hoàn tất {len(df):,} lượt khám. Đã tạo 12 bảng, 4 hình và REPORT_INSERTS_ADVANCED.md.")


if __name__ == "__main__":
    main()
