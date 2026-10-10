# Kế hoạch tích hợp PPTX V2 (cập nhật trước Task 2)

Tài liệu này cập nhật Task 1 theo **quyết định đã chốt** của ứng viên.  
Chưa triển khai code cho đến khi các điểm *cần xác nhận* (mục 5) được trả lời hoặc chấp nhận phương án tạm ghi trong mục đó.

Nguồn xác minh template: `docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx` (1 slide, shape name thực tế = `Google Shape;{id};p1`, **không** có `txt_*`).

---

## 1. Quyết định đã chốt

| # | Quyết định |
|---|------------|
| 1 | Ánh xạ bằng **shape ID** đã inventory; mapping tập trung; kiểm tra shape tồn tại trước khi ghi; không giả định `txt_*`. |
| 2 | Tối đa **3** sản phẩm; nếu `len(items) > 3` → **fail job** với message rõ; **không** cắt danh sách. |
| 3 | `unit_price` = giá **chưa VAT**. Không tự nhân `× 1.08`. Không ghi giá chưa VAT vào cột mang nhãn gồm VAT. |
| 4 | Quy cách: parse số kg/bao từ `specification` nếu hợp lệ; không parse được → `"25"` + **log** default. |
| 5 | Nguồn mã = `quotation.id` (tương lai). **Tạm C-B:** không ghi đè shape 46 cho đến khi có quy tắc mapping chính thức. |
| 6 | Không đưa `payment_terms` / `delivery_terms` / `note` lên slide V2; giữ nguyên trong DB/API/UI. |
| 7 | **VAT = V-A:** để trống shape 30/34/38 (xóa sample, không ghi số). |
| 8 | **Ngày:** điền ngày/tháng từ `created_at`; **giữ literal `năm 2026`** trên template. |

---

## 2. Mapping tập trung (shape ID → dữ liệu)

### 2.1. Bảng mapping — điền được / rule đã chốt

| Shape ID | Vai trò (theo text template) | Nguồn dữ liệu | Hành vi điền (chốt / tạm) |
|----------|------------------------------|---------------|---------------------------|
| **20** | `Quý khách hàng / Quý đối tác: […]` | `customer.company` | Thay phần placeholder `[…]` (hoặc toàn bộ phần sau nhãn cố định nếu cần để tránh sót `[]`). **Giữ** prefix nhãn đã xác minh. |
| **28** | Tên hàng dòng 1 | `items[0].product_name` | Ghi đè toàn bộ text frame (hiện là `[…]` mẫu). |
| **32** | Tên hàng dòng 2 | `items[1].product_name` nếu có | Nếu thiếu item: **xóa/blank** ô sản phẩm dòng đó (không để sample `[TSPP]`…). |
| **36** | Tên hàng dòng 3 | `items[2].product_name` nếu có | Như trên. |
| **29** | Đơn giá chưa VAT dòng 1 | `items[0].unit_price` | Format hiển thị số (vd. có dấu phẩy nghìn) — chỉ format, không đổi giá trị thương mại. |
| **33** | Đơn giá chưa VAT dòng 2 | `items[1].unit_price` nếu có | Blank nếu không có dòng. |
| **37** | Đơn giá chưa VAT dòng 3 | `items[2].unit_price` nếu có | Blank nếu không có dòng. |
| **30** | Đơn giá gồm VAT dòng 1 | — | **V-A:** để trống (không ghi `unit_price`). |
| **34** | Đơn giá gồm VAT dòng 2 | — | **V-A:** để trống. |
| **38** | Đơn giá gồm VAT dòng 3 | — | **V-A:** để trống. |
| **49** | Quy cách dòng 1 | parse `items[0].specification` else `"25"` | Log khi fallback default. |
| **50** | Quy cách dòng 2 | parse `items[1].specification` else `"25"` | Chỉ khi có item dòng 2; nếu không có item → blank (không ép 25 cho dòng trống). |
| **51** | Quy cách dòng 3 | parse `items[2].specification` else `"25"` | Như dòng 2. |
| **42** | `Ngày […] tháng […] năm 2026` | `quotation.created_at` → day, month | Điền ngày/tháng; **giữ** `năm 2026` literal. |
| **46** | `ABC-[]/QT/[2606]-[01]` | `quotation.id` (chưa dùng) | **C-B:** không ghi đè shape này. |

### 2.2. Cấu trúc ô mã (shape 46) — đã xác minh XML

- Một text run duy nhất: `ABC-[]/QT/[2606]-[01]`
- Thành phần nhìn như cố định: tiền tố `ABC-`, đoạn `/QT/`, dấu `-` giữa hai bracket cuối
- Thành phần trong ngoặc: `[]`, `[2606]`, `[01]` (sample)

**Chưa xác minh nghiệp vụ:** ý nghĩa từng bracket và cách derive từ `quotation.id`.

### 2.3. Không map lên slide (giữ trong hệ thống)

| Field hệ thống | Lý do |
|----------------|--------|
| `payment_terms` | Template đã có khối điều khoản cố định (shape 41); không có ô riêng |
| `delivery_terms` | Như trên |
| `note` (+ AI normalize) | Không có vị trí trên V2; vẫn lưu DB / có thể dùng sau |
| `quantity` | Không có cột SL trên slide V2 |
| `customer.email` / `phone` / `address` / `name` | Greeting dùng company (chốt đề xuất: **company**); name không có ô |

### 2.4. Shape cố định — không ghi

Header công ty, tiêu đề, đoạn mở đầu, header cột, STT `1/2/3`, khối điều khoản (41), chữ ký/slogan/footer, ảnh logo/stamp.

### 2.5. Contract mapping runtime **[Đề xuất triển khai Task 2]**

Module tập trung (vd. `worker/jobs/pptx_mapping.py`):

```text
SHAPE_MAP = {
  20: FieldSpec(...),
  28: FieldSpec(...),
  ...
}
```

Trước khi ghi mỗi shape:

1. Tìm shape theo `id` trong slide XML / API thư viện.
2. Nếu **không tồn tại** → fail job (`missing shape id=…`).
3. Nếu tồn tại → set text theo rule field.
4. Sau khi fill: không đụng shape ngoài danh sách.

`len(items) > 3` → fail **trước** khi mở/ghi template:
`Quotation has N items; PPTX V2 template supports at most 3`.

---

## 3. Xử lý quy cách (đã chốt)

**Parse hợp lệ (đề xuất rule kỹ thuật, không đổi giá trị thương mại):**

- Lấy số từ `specification` nếu match kiểu: số nguyên/thập phân đứng riêng hoặc kèm đơn vị `kg`, `kg/bao`, `/bao` (case-insensitive).
- Ví dụ chấp nhận: `"25"`, `"25kg"`, `"25 kg/bao"`, `"25.0"`.
- Không chấp nhận: `"99.5%"`, `"TSPP grade A"` → fallback `"25"` + log  
  `specification_defaulted quotation_id=… item_index=… raw=… default=25`.

Dòng không có item tương ứng: **không** ghi `"25"`; để trống / xóa sample.

---

## 4. Danh sách test cập nhật

### 4.1. Mapping / worker

| ID | Test | Kỳ vọng |
|----|------|---------|
| W1 | 1 item hợp lệ | Shape 28/29/49 điền; 32–38 & 50–51 dòng trống (không còn sample `[STPP]` / `[51,560]`) |
| W2 | đúng 3 items | Cả 3 dòng điền |
| W3 | 4+ items | Job **FAILED**; message chứa max 3; **không** tạo file / hoặc không complete |
| W4 | Shape id bắt buộc bị xóa khỏi template giả | Fail rõ `missing shape` |
| W5 | `specification="25 kg/bao"` | Quy cách = `25` |
| W6 | `specification="99.5%"` | Quy cách = `25` + log default |
| W7 | Cột chưa VAT | Text = format(`unit_price`) |
| W8 | Cột gồm VAT | **Không** bằng `unit_price` khi chưa có rule VAT; theo phương án tạm §5.1 đã chọn |
| W9 | Customer company | Shape 20 chứa company; không còn `[…]` sample |
| W10 | Date từ `created_at` | Shape 42 có ngày/tháng; giữ wording cố định đã chốt |
| W11 | Mã báo giá | Theo phương án tạm §5.2 đã chọn; assert không invent `ABC-…` trừ khi rule đã xác nhận |
| W12 | payment/delivery/note | Không xuất hiện như nội dung mới trên slide (so với baseline cố định) |
| W13 | File output | `.pptx`, ZIP OOXML hợp lệ, size > 0 |
| W14 | Fixed strings còn | `BẢNG BÁO GIÁ`, đoạn điều khoản đặc trưng vẫn còn |

### 4.2. API / FE (Task 3)

| ID | Test |
|----|------|
| A1 | Allowlist chỉ `{id}.pptx` |
| A2 | Download MIME PowerPoint + filename `.pptx` |
| A3 | Path traversal / wrong extension → 400 |
| E1 | E2E create → COMPLETED → download PPTX |
| E2 | FAIL (4 items hoặc inject) → retry path vẫn đúng với PPTX |
| E3 | Inactive customer blocked |

### 4.3. Cách assert không mở PowerPoint

Parse `ppt/slides/slide1.xml` trong file output: đọc text theo shape `id`, so khớp chuỗi mong đợi.

---

## 5. Điểm nghiệp vụ còn cần xác nhận (liệt kê riêng)

### 5.1. VAT — **Đã chốt V-A**

Cột gồm VAT (30/34/38): **để trống**. Không ghi `unit_price`, không nhân thuế.  
Vẫn chờ rule/thuế suất hoặc field API trước khi điền số thật (tương lai V-D).

---

### 5.2. Format mã báo giá — **Đã chốt C-B**

Shape 46 **không bị ghi đè**. Sample `ABC-[]/QT/[2606]-[01]` còn trên file đến khi có quy tắc map từ `quotation.id`.

---

### 5.3. Năm trên shape 42 — **Đã chốt**

Điền ngày/tháng từ `created_at`; **giữ literal `năm 2026`**.

---

### 5.4. Dòng sản phẩm thiếu (< 3)

**Đề xuất đã ghi trong mapping:** blank các ô tên/giá/quy cách của dòng trống; không để dữ liệu sample.  
Cần xác nhận nếu muốn ẩn cả số STT (hiện STT 1/2/3 là shape cố định — **không** đụng trừ khi được yêu cầu).

---

### 5.5. Greeting: `company` vs `name`

**Đề xuất tạm:** dùng `customer.company` cho shape 20.  
Xác nhận nếu cần `name` hoặc `"{company} ({name})"`.

---

## 6. Thứ tự triển khai (chỉ sau khi chốt §5.1 và §5.2)

1. **Chốt option VAT (V-A/B/C) và mã (C-A/B/C)** — ghi vào PR/README demo.
2. **Task 2:** mapping module + fill PPTX theo shape ID + fail >3 items + validator + tests W*.
3. **Task 3:** allowlist/MIME/FE `.pptx` + E2E.
4. **Task 4:** docs/sample/demo script; nêu rõ Mock/deterministic; nêu VAT & mã nếu vẫn đang phương án tạm.

---

## 7. Dependency dự kiến (Task 2 — chưa cài trong task này)

- Thêm thư viện thao tác PPTX (ứng viên đề xuất khi code: thường `python-pptx`) **hoặc** chỉnh XML trong ZIP nếu muốn zero-dep — quyết định lúc Task 2, ưu tiên ít rủi ro vỡ layout.
- Giữ `python-docx` chỉ nếu còn dùng template DOCX cũ; có thể deprecate sau khi PPTX ổn định.

---

## 8. Trạng thái Task 2

| Hạng mục | Status |
|----------|--------|
| Shape ID fill + no `txt_*` | **Implemented** |
| Max 3 items fail | **Implemented** |
| Quy cách parse + default 25 | **Implemented** |
| VAT = V-A (trống 30/34/38) | **Implemented** |
| CODE = C-B (không đụng 46) | **Implemented** |
| Ngày/tháng + năm 2026 | **Implemented** |
| Backend allowlist `.pptx` | **Implemented** (hook tối thiểu) |
| FE label Download (.pptx) | **Task 3** |
