# Báo cáo bài tập lớn – Hệ thống quản lý kho thông minh

## Biên dịch
Dùng **XeLaTeX** (bắt buộc, vì phông Unicode tiếng Việt qua `fontspec`/`polyglossia`).

    latexmk -xelatex main
    # hoặc
    xelatex main && bibtex main && xelatex main && xelatex main

Trên Overleaf: Menu → Compiler → **XeLaTeX**.

Kiểu tài liệu tham khảo: `IEEEtran` (có sẵn trên Overleaf và TeX Live đầy đủ).
Nếu máy thiếu `IEEEtran.bst`, tạm đổi thành `ieeetr` trong `main.tex`.

## Cấu trúc
| Thư mục / file | Nội dung |
|---|---|
| `main.tex` | File chính |
| `preamble.tex` | Gói, phông, lề, kiểu TikZ cho BPC, BLD, ER, LCT |
| `references.bib` | Tài liệu tham khảo (IEEE) |
| `frontmatter/` | Thông tin chung (`thongtin.tex`), bìa, danh mục từ viết tắt |
| `chapters/` | Ch.1 Giới thiệu, Ch.2 Cơ sở lý thuyết, **Ch.3–8 = Giai đoạn 1–6 của giáo trình**, Ch.9 Kết luận |
| `figures/` | 16 hình vẽ bằng TikZ/forest, mỗi hình một file; logo trường |
| `appendix/` | Phụ lục A câu hỏi khảo sát; B script CSDL (`schema.sql` = `db/schema/01_schema.sql` của mã nguồn); C mã nguồn module trọng yếu; D hướng dẫn cài đặt, chạy thử |
| `appendix/code/` | Bản sao các file Python trích trong Ch.7 và Phụ lục C; `code/tex/` là bản tô màu sẵn bằng Pygments |

## Mã Python trong báo cáo
Gói `listings` không hiển thị đúng chữ tiếng Việt trong mã dưới XeLaTeX, nên mã Python được tô màu trước bằng Pygments thành `appendix/code/tex/*.tex` và chèn bằng lệnh `\maPy{chú thích}{nhãn}{tên file}`. Không cần `-shell-escape`. Nếu sửa file `.py` trong `appendix/code/`, sinh lại bằng:

    cd appendix/code
    for f in *.py; do pygmentize -l python -f latex -P 'verboptions=frame=single,framerule=0.3pt,rulecolor=\color{black!40},fontsize=\footnotesize,breaklines=true' $f > tex/${f%.py}.tex; done

## Thông tin bìa
Sửa **một file duy nhất**: `frontmatter/thongtin.tex` (tên đề tài, học phần, lớp, giảng viên, 5 sinh viên: họ tên viết HOA, MSSV, email). Trang bìa và metadata PDF tự cập nhật. Logo trường: `figures/logo-hust.png`.

## Quy ước
- Chỗ đánh dấu bằng `\canbosung{...}` (chữ đỏ) là nội dung cần bổ sung trước khi nộp.
- Lề, cỡ chữ, giãn dòng theo quy ước đồ án thường gặp; **đối chiếu mẫu trình bày của khoa** và sửa trong `preamble.tex`.
- Mọi sơ đồ dùng ký pháp của giáo trình, định nghĩa một lần trong `preamble.tex`.

## Biên dịch trên Overleaf bản miễn phí

- Menu → Settings → **Compiler: XeLaTeX**, Main document: `main.tex`.
- File `latexmkrc` cho Overleaf chỉ chạy XeLaTeX **một lượt** mỗi lần Recompile, dùng sẵn `main.aux`, `main.toc`, `main.bbl`… đi kèm; sau khi sửa nội dung, bấm Recompile thêm một lần để Mục lục và số trang cập nhật.
- Để không vượt giới hạn thời gian biên dịch, các hình TikZ đã được biên dịch sẵn thành `figures/<tên>.pdf`;
  `main.tex` chèn các file PDF này (lệnh `\vehinh` trong `preamble.tex`).
- **Sửa một hình:** sửa `figures/<tên>.tex`, đổi Main document sang `xuat_hinh.tex`, Recompile, tải PDF về
  (mỗi trang là một hình, theo thứ tự trong `xuat_hinh.tex`), tách trang tương ứng và tải lên thay `figures/<tên>.pdf`;
  rồi đổi Main document về `main.tex`. Hoặc đặt `\VeTikZtrue` trong `preamble.tex` để vẽ trực tiếp (chậm, chỉ dùng khi biên dịch trên máy).
