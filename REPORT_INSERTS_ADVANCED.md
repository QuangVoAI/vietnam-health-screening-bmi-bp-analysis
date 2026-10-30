# Kết quả bổ sung đã chạy thật để chèn vào báo cáo

Tệp này được tạo tự động từ `run_m3_advanced_validation.py` trên CSV nghiên cứu đã khử định danh (*n* = 7,146). Các kết quả dưới đây là phân tích phụ trợ của mối liên quan cắt ngang BMI–HATT, không phải mô hình chẩn đoán hoặc dự báo lâm sàng.

## Chèn vào phần phân phối

Trong ba phân phối ứng viên được so sánh bằng AIC, phân phối có AIC thấp nhất là **Lognormal (loc=0)** cho BMI và **Lognormal (loc=0)** cho HATT. Đây là kết quả so sánh mô tả giữa các phân phối ứng viên; không nên diễn giải là dữ liệu tuân theo hoàn hảo một phân phối cụ thể. Chi tiết: `tables/15_distribution_fit_aic.csv`; hình: `figures/15_distribution_fit_candidates.png`.

## Chèn vào phần kiểm định giới tính và xu hướng

Kiểm định Levene dựa trên trung vị cho HATT theo giới có *W* = 0.073, *p* = 0.788. Welch t-test cho chênh lệch trung bình Nam − Nữ là 9.784 mmHg, KTC 95% [9.062; 10.505], *t* = 26.581, df = 7123.95, *p* < 0.001. Mann–Whitney đối chiếu cũng cho *p* < 0.001; rank-biserial = 0.391. Chi tiết: `tables/16_sex_tests_extended.csv`.

Kiểm định xu hướng Cochran–Armitage theo thứ tự năm nhóm BMI cho *z* = 18.313, *p* < 0.001, phù hợp với xu hướng tăng tỷ lệ cờ sàng lọc khi nhóm BMI tăng. Tỷ lệ cờ sàng lọc chung là 19.54%. Chi tiết: `tables/17_bmi_screening_trend_test.csv`.

## Chèn vào phần tương quan

Pearson BMI–HATT toàn mẫu là *r* = 0.287, KTC 95% [0.265; 0.308], *p* < 0.001; Spearman là ρ = 0.335, *p* < 0.001. Sau khi điều chỉnh tuổi, giới và mạch bằng phương pháp phần dư, tương quan riêng phần là *r* = 0.233, *p* < 0.001. Theo giới, Pearson BMI–HATT là 0.256 ở nam và 0.240 ở nữ. Chi tiết: `tables/18_correlations_extended.csv`.

## Chèn vào phần hồi quy và chẩn đoán

Mô hình OLS đầy đủ có *F*(4, 7141) = 616.106, *p* < 0.001; R² = 0.257, R² hiệu chỉnh = 0.256 và RMSE = 14.068 mmHg. Với BMI, hệ số OLS là 0.861 mmHg cho mỗi 1 kg/m²; KTC 95% HC3 [0.771; 0.951], rất gần KTC OLS [0.778; 0.944]. Chi tiết: `tables/19_ols_hc3_robust_inference.csv`.

Breusch–Pagan cho LM = 277.125, *p* < 0.001, cho thấy phương sai phần dư không hoàn toàn đồng nhất; vì vậy nên báo cáo KTC HC3 song song với OLS. Cook's D lớn nhất là 0.023, nhỏ hơn 1, nên không có quan sát nào chi phối cực mạnh; tuy nhiên 422 lượt vượt ngưỡng sàng lọc 4/*n* và cần được diễn giải là ảnh hưởng vừa phải, không phải tự động xóa. Skewness phần dư là 0.744. Hình chẩn đoán: `figures/16_regression_diagnostics_extended.png`; bảng: `tables/20_regression_diagnostics_extended.csv`.

## Chèn vào phần so sánh mô hình và kiểm định chéo

BMI một mình giải thích R² = 0.082; thêm tuổi và giới nâng R² lên 0.231; thêm mạch đạt R² = 0.257. Với 5-fold cross-validation có xáo trộn cố định (*seed* = 42), RMSE ngoài fold trung bình là 14.064 mmHg, MAE là 10.693 mmHg, R² ngoài fold là 0.255. Các chỉ số này gần với trong mẫu, nhưng sai số khoảng 14 mmHg vẫn quá lớn để sử dụng cho dự báo huyết áp của một cá nhân. Bảng: `tables/21_model_comparison.csv`, `tables/22_five_fold_cross_validation.csv`; hình: `figures/17_cv_observed_vs_predicted.png`.

## Chèn vào phần độ nhạy

Hệ số BMI chính là 0.861 mmHg/1 BMI. Hệ số vẫn gần tương tự khi bỏ lượt có cờ mã nguồn lặp (0.852), winsorize HATT tại P1–P99 (0.856) và loại HATT ngoài hàng rào IQR (0.815). Trên thang log(HATT), mỗi 1 kg/m² BMI liên quan với HATT cao hơn khoảng 0.719%. Đây là phân tích độ bền của mối liên quan trong mẫu, không chứng minh quan hệ nhân quả. Chi tiết: `tables/23_sensitivity_extended.csv`.

## Phần không được tự điền

Từ CSV phân tích cuối chỉ có thể kiểm chứng *n* = 7.146. Tiêu chí cụ thể làm loại 28 bản ghi cuối và lý do thiếu số đo của 3.582 bản ghi nguồn không thể suy ra từ CSV đã lọc; chỉ điền nội dung này khi có audit/provenance từ tệp nguồn, nếu không hãy nêu là giới hạn chọn mẫu.
