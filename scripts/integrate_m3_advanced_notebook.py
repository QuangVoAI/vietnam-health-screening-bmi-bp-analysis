"""Attach executed advanced-validation outputs to the final notebook."""

from pathlib import Path
import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "M3_BMI_HuyetAp_Final_Analysis.ipynb"
TAG = "ADVANCED_VALIDATION_20261031"


def md(text):
    cell = nbformat.v4.new_markdown_cell(text)
    cell.metadata["m3_advanced_validation"] = True
    return cell


def code(text):
    cell = nbformat.v4.new_code_cell(text)
    cell.metadata["m3_advanced_validation"] = True
    return cell


def find(cells, phrase):
    return next(i for i, cell in enumerate(cells) if phrase in cell.source)


nb = nbformat.read(NOTEBOOK, as_version=4)
nb.cells = [c for c in nb.cells if not c.get("metadata", {}).get("m3_advanced_validation") and TAG not in c.get("metadata", {}).get("tags", [])]

# The former basic sensitivity section is superseded by the extended,
# reproducible sensitivity analysis inserted below. Remove only that heading,
# its calculation cell, and its interpretation—not the aggregate export cell.
old_sensitivity_heading = next(
    (i for i, cell in enumerate(nb.cells) if "## 6. Phân tích độ nhạy và kết luận" in cell.source),
    None,
)
if old_sensitivity_heading is not None:
    del nb.cells[old_sensitivity_heading:old_sensitivity_heading + 3]

# Repair the heading hierarchy after removing the old section.
for cell in nb.cells:
    if cell.cell_type != "markdown":
        continue
    cell.source = cell.source.replace("## 7. Trực quan hóa mở rộng", "## 6. Trực quan hóa mở rộng")
    cell.source = cell.source.replace("## 8. Đối chiếu với nghiên cứu", "## 7. Đối chiếu với nghiên cứu")
    cell.source = cell.source.replace("## 9. Kết luận báo cáo", "## 8. Kết luận báo cáo")

# Correct the former diagnostics wording before adding the reproducible extension.
old = find(nb.cells, "### Diễn giải chẩn đoán mô hình")
nb.cells[old].source = """### Diễn giải chẩn đoán mô hình

VIF được kiểm tra để đánh giá đa cộng tuyến giữa các biến giải thích; residual-versus-fitted plot và Q–Q plot dùng để đánh giá phần dư. Phần giữa của phần dư nhìn chung xoay quanh 0, nhưng phần đuôi lệch khỏi đường chuẩn. Breusch–Pagan và khoảng tin cậy HC3 được bổ sung ở phần sau để kiểm tra chính thức phương sai không đồng nhất. Các biến chưa đo lường (ví dụ thuốc, ăn mặn, hút thuốc, rượu, vận động, bệnh nền) có thể giải thích phần biến thiên còn lại."""

advanced_cells = [
    md("""### 5a. Kiểm tra bền vững và khả năng tổng quát hóa

Phần này giữ nguyên mô hình chính `HATT ~ BMI + tuổi + giới + mạch`. Phân tích bổ sung gồm so sánh phân phối ứng viên, kiểm định đối chiếu, sai số chuẩn HC3, Breusch–Pagan, Cook’s distance, so sánh mô hình, 5-fold cross-validation và các kịch bản độ nhạy. Đây là kiểm tra kỹ thuật của liên hệ cắt ngang trong mẫu; không tạo ra mô hình chẩn đoán hay dự báo lâm sàng."""),
    code("""# Chạy phân tích bổ sung từ mã nguồn tái lập; chỉ sinh bảng/hình tổng hợp, không xuất dữ liệu vi mô.
import runpy
from IPython.display import Image, display

ADVANCED_SCRIPT = PROJECT_ROOT / 'run_m3_advanced_validation.py'
assert ADVANCED_SCRIPT.exists(), f'Không tìm thấy {ADVANCED_SCRIPT}'
runpy.run_path(str(ADVANCED_SCRIPT), run_name='__main__')
RESULT_DIR = OUT_DIR / 'tables'

advanced_tables = {
    'So sánh phân phối bằng AIC': '15_distribution_fit_aic.csv',
    'Kiểm định giới và Mann–Whitney': '16_sex_tests_extended.csv',
    'Xu hướng BMI × cờ sàng lọc': '17_bmi_screening_trend_test.csv',
    'Tương quan phân tầng và riêng phần': '18_correlations_extended.csv',
    'OLS với CI HC3': '19_ols_hc3_robust_inference.csv',
    'Breusch–Pagan và Cook’s distance': '20_regression_diagnostics_extended.csv',
    'So sánh mô hình lồng nhau': '21_model_comparison.csv',
    '5-fold cross-validation': '22_five_fold_cross_validation.csv',
    'Độ nhạy mở rộng': '23_sensitivity_extended.csv',
}
for title, filename in advanced_tables.items():
    print(f'\\n{title}')
    display(pd.read_csv(RESULT_DIR / filename).round(4))"""),
    md("""**Kết quả chính.** Lognormal có AIC thấp nhất trong ba phân phối ứng viên cho cả BMI và HATT; đây chỉ là mô tả, không phải khẳng định phân phối hoàn hảo. Mann–Whitney và Cochran–Armitage xác nhận các kết luận Welch t-test/Chi-square. Tương quan riêng phần BMI–HATT sau điều chỉnh tuổi, giới và mạch là **r = 0,233**. Hệ số BMI với CI HC3 là **0,861 mmHg/1 BMI**; CI 95% HC3 **[0,771; 0,951]**, rất gần CI OLS, nên kết luận chính không đổi."""),
    code("""# Hình mới phục vụ phụ lục/báo cáo. Các hình thể hiện kết quả bổ sung, không thay thế hình cốt lõi.
for filename in [
    '14_outlier_review.png',
    '15_distribution_fit_candidates.png',
    '16_regression_diagnostics_extended.png',
    '17_cv_observed_vs_predicted.png',
]:
    display(Image(filename=str(FIG_DIR / filename), width=900))"""),
    md("""**Chẩn đoán và đánh giá ngoài fold.** Breusch–Pagan cho *p* < 0,001, do đó phương sai phần dư không hoàn toàn đồng nhất và CI HC3 nên được ưu tiên khi diễn giải suy luận. Cook’s D lớn nhất = **0,023** (<1), không có điểm chi phối cực mạnh. Mô hình đầy đủ có R² = **0,257**; qua 5-fold CV, RMSE = **14,064 mmHg**, MAE = **10,693 mmHg**, R² = **0,255**. Chỉ số CV gần trong mẫu, nhưng sai số vẫn lớn ở cấp cá nhân; mô hình chỉ dùng để mô tả liên hệ/định hướng sàng lọc quần thể."""),
    md("""**Độ nhạy mở rộng.** Hệ số BMI lần lượt là **0,861** (mô hình chính), **0,852** (bỏ cờ lặp), **0,856** (winsorize HATT P1–P99) và **0,815** (bỏ HATT ngoài hàng rào IQR). Trên thang log(HATT), mỗi 1 kg/m² BMI liên quan với HATT cao hơn khoảng **0,719%**. Hướng kết quả ổn định, nhưng đây không phải bằng chứng nhân quả."""),
]

anchor = find(nb.cells, "# Xuất bảng kết quả")
nb.cells[anchor:anchor] = advanced_cells
nbformat.write(nb, NOTEBOOK)
print(NOTEBOOK)
