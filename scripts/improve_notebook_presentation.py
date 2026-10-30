"""Add reader-facing interpretation cells and consistent hierarchy to the executed notebook."""
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parent
PATH = ROOT / 'outputs/M3_BMI_HuyetAp_Final_Project/M3_BMI_HuyetAp_Final_Analysis.ipynb'
nb = nbformat.read(PATH, as_version=4)

TAG = 'NOTEBOOK_PRESENTATION_UPGRADE'
# Idempotency: remove only prior interpretation cells inserted by this script.
nb.cells = [c for c in nb.cells if TAG not in c.get('metadata', {}).get('tags', [])]

def insight(text):
    cell = nbformat.v4.new_markdown_cell(text)
    cell.metadata['tags'] = [TAG]
    return cell

def find_index(fragment):
    return next(i for i, c in enumerate(nb.cells) if fragment in c.source)

# Correct the section-numbering hierarchy.
for cell in nb.cells:
    if cell.cell_type != 'markdown':
        continue
    cell.source = cell.source.replace('## 6. Trực quan hóa mở rộng', '## 7. Trực quan hóa mở rộng')
    cell.source = cell.source.replace('## 7. Đối chiếu với nghiên cứu', '## 8. Đối chiếu với nghiên cứu')
    cell.source = cell.source.replace('### Kết luận báo cáo', '## 9. Kết luận báo cáo')

inserts = [
    ('summary.round(2)', insight('''### Diễn giải chất lượng dữ liệu\n\nTập phân tích có **7.146 lượt khám và 14 biến**, không thiếu dữ liệu ở các biến phân tích và không có mã nghiên cứu trùng. Có **118 lượt mang cờ mã nguồn lặp**; đây là lý do phân tích độ nhạy được thực hiện ở Mục 6. Các cờ IQR là ngoại lai **thống kê**, không phải bằng chứng sai số hay bất thường lâm sàng, nên được giữ lại trong phân tích chính để tránh loại bỏ dữ liệu tùy tiện.''')),
    ("print('Kết luận: BMI và HATT đều lệch phải", insight('''### Diễn giải phân phối\n\nBMI (skewness = **1,058**) và HATT (skewness = **0,820**) đều lệch phải; các Q–Q plot cũng cho thấy lệch ở phần đuôi. Vì cỡ mẫu lớn, kiểm định chuẩn tính rất nhạy và p-value nhỏ không nên được diễn giải tách rời. Do đó, notebook báo cáo đồng thời các phương pháp ít phụ thuộc hơn vào chuẩn tính nghiêm ngặt: Welch t-test/Welch ANOVA, Spearman và khoảng tin cậy của hồi quy.''')),
    ('ttest_results', insight('''### Kết quả Welch t-test\n\nHATT trung bình ở nam cao hơn nữ (lần lượt khoảng **125,16** so với **115,37 mmHg**). Khác biệt có ý nghĩa thống kê, *t* = **26,581**, *p* < 0,001, với **Cohen’s d = 0,629**. Kích thước hiệu ứng này cho thấy khác biệt có ý nghĩa thực hành ở mức vừa, thay vì chỉ là hệ quả của cỡ mẫu lớn.''')),
    ('display(posthoc_tables[grouping])', insight('''### Diễn giải ANOVA, Welch ANOVA và hậu kiểm\n\nANOVA cho thấy HATT khác theo nhóm BMI (*F* = **162,401**, η² = **0,083**) và nhóm tuổi (*F* = **186,611**, η² = **0,073**), đều *p* < 0,001. Vì Levene cho thấy phương sai không đồng nhất, Welch ANOVA được dùng như kiểm tra bền vững và xác nhận cùng kết luận tổng quát. Bảng hậu kiểm Welch–Holm nêu rõ những cặp nhóm khác nhau sau khi hiệu chỉnh cho nhiều so sánh; không nên chỉ kết luận chung rằng “mọi nhóm đều khác nhau” nếu chưa xem từng cặp.''')),
    ("ct.assign(**{'Tỷ lệ sàng lọc (%)'", insight('''### Kết quả Chi-square\n\nNhóm BMI và cờ sàng lọc HA ≥140/90 có liên quan: χ²(4) = **337,862**, *p* < 0,001; **Cramér’s V = 0,217**. Điều kiện Chi-square đạt vì ô kỳ vọng nhỏ nhất là **83,03** và không có ô nào dưới 5. Tỷ lệ cờ sàng lọc tăng theo nhóm BMI, từ **6,6%** ở BMI <18,5 đến **38,3%** ở BMI ≥30. Đây là một mô hình sàng lọc trong mẫu, không phải tỷ lệ chẩn đoán tăng huyết áp.''')),
    ('corr_results.round(4)', insight('''### Diễn giải tương quan\n\nBMI và HATT có liên hệ dương ở mức thấp–vừa: Pearson *r* = **0,287** và Spearman ρ = **0,335**, đều *p* < 0,001. Spearman cao hơn Pearson, phù hợp với xu hướng đơn điệu trong khi phân phối không hoàn toàn chuẩn. Kết quả không nói rằng BMI quyết định hoàn toàn HATT; độ phân tán trên scatter plot cho thấy còn nhiều yếu tố khác chưa đo lường.''')),
    ('regression.round(4)', insight('''### Diễn giải hồi quy đa biến\n\nSau khi xét đồng thời tuổi, giới và mạch, mỗi tăng **1 kg/m² BMI** liên quan với tăng **0,861 mmHg HATT** (CI 95%: **0,778–0,944**; *p* < 0,001). Mô hình có R² = **0,257**, R² hiệu chỉnh = **0,256** và RMSE = **14,07 mmHg**. Đây là mức giải thích vừa phải: mô hình hữu ích để mô tả liên hệ trong mẫu nhưng không phải công cụ chẩn đoán hoặc dự báo lâm sàng đầy đủ.''')),
    ("fig.savefig(FIG_DIR/'04_regression_diagnostics.png'", insight('''### Diễn giải chẩn đoán mô hình\n\nVIF được kiểm tra để đánh giá đa cộng tuyến giữa các biến giải thích; phần dư được xem qua residual-versus-fitted plot và Q–Q plot. Phần giữa của phần dư nhìn chung xoay quanh 0, nhưng phần đuôi lệch khỏi đường chuẩn. Vì vậy, hệ số và CI được diễn giải thận trọng như bằng chứng về **mối liên quan thống kê**, đồng thời cần ghi nhận rằng các biến chưa có trong dữ liệu (ví dụ thuốc, ăn mặn, hút thuốc, rượu, vận động, bệnh nền) có thể giải thích phần biến thiên còn lại.''')),
    ('sensitivity', insight('''### Diễn giải độ nhạy\n\nHệ số BMI của mô hình chính là **0,861 mmHg/1 BMI**; sau khi loại 118 lượt mang cờ lặp, hệ số là **0,852**. Mức thay đổi rất nhỏ cho thấy kết luận chính về liên hệ BMI–HATT không phụ thuộc đáng kể vào quyết định giữ hay bỏ các lượt này.''')),
]

# Insert in reverse document order to keep located positions valid.
for marker, cell in reversed(inserts):
    pos = find_index(marker)
    nb.cells.insert(pos + 1, cell)

nbformat.write(nb, PATH)
print(PATH)
