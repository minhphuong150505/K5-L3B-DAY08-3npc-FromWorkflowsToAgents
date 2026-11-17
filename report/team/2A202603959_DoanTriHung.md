# Báo cáo cá nhân — 2A202603959_DoanTriHung

## 1. Thông tin thành viên

- Họ tên: Đoàn Trí Hùng
- MSSV: 2A202603959
- Email: 26ai.hungdt2@vinuni.edu.vn
- GitHub: `hungdt31`

## 2. Phần việc phụ trách

Vai **P3 · Orchestrator + Handoff + Research card** (theo `TEAM.md`):

- Shape C `src/lab8/shapes/orchestrator.py`: orchestrator giao việc cho investigator chỉ đọc qua handoff `handoff.v1`, orchestrator tự quote và là shape duy nhất gọi cửa ghi của host.
- Test riêng cho ranh giới handoff và trace: `src/tests/test_orchestrator_handoff_extra.py`.
- Phiếu nghiên cứu `report/team/research_card.md` (R1 · Scaling) và ablation workflow so với orchestrator.

## 3. Đóng góp cụ thể

### Commit chính (nhánh `feat/orchestrator`)

| Hash | Nội dung |
| --- | --- |
| `c9fccb7` | Bước 1: khung `run_claim` / `_run`, mở và đóng connection, `Budget`, `Trace`, hàm `done()` để mọi nhánh return đều đi qua `finish()` |
| `6dfb88d` | Bước 2: đọc claim qua `get_claim_view`; `unknown_claim` → `failed`, thiếu `order_id` → `needs_info`; một lời gọi model `plan` |
| `dd6f0f8` | Bước 3: `make_handoff` với tool chỉ đọc, `run_readonly_investigators`, order không visible → `escalated` |
| `92519ab` | Bước 4: `compute_compensation` từ order row, quote 0 → `denied`, quote > 0 → `durability.issue_refund` với quote đầy đủ và `crash_at` |
| `c697f75` | Test `test_orchestrator_handoff_extra.py` (10 test) |
| `e5f3f8f` | Điền research card R1 và kết quả ablation |

### Test đã thêm

`src/tests/test_orchestrator_handoff_extra.py`, chạy trong cổng host `python -m pytest -q`:

- `test_orchestrator_trace_has_no_secret_or_pii` (C-001, C-004, C-005, C-010, C-014): trace có `run_id` khớp kết quả; không chứa `CANARY_SECRET_`, `parent_secret`, `raw_headers`, và không chứa phone, address, internal_note, item_name của bất kỳ order nào trong dữ liệu public.
- `test_traced_handoff_is_allowlisted_and_read_only`: trace có đúng một handoff `handoff.v1`, không có write tool, không có ticket.
- `test_handoff_drops_fact_keys_outside_allowlist`: `make_handoff` loại `phone` và `ticket` khỏi `facts`.
- `test_investigator_cannot_be_given_write_tool` (`issue_refund`, `append_audit`): ném `HandoffError`.
- `test_ticket_delay_does_not_override_order_row`: C-002 seed 55 (ticket ghi trễ 5 ngày, order ghi 2 ngày) → `denied`, không có dòng ledger. Đây là trial mà swarm tham chiếu làm sai.

### Quyết định kỹ thuật

- **`facts={}` trong handoff.** Lúc giao việc, orchestrator chưa có dữ kiện nào đã kiểm chứng. Chuyển số liệu từ ticket sang investigator là cho dữ liệu người dùng vượt ranh giới. Investigator tự đọc order từ DB trong phạm vi `principal_id` của claim.
- **Investigator chỉ nhận `lookup_order`, `lookup_refund_history`, `lookup_policy`.** Bỏ `get_clause` vì `run_readonly_investigators` không chạy tool này, và clause cũ (`SHIP-LATE-OLD`) dễ bị dùng sai nếu không tự kiểm `is_current`.
- **Orchestrator tự quote, không dùng quote của investigator.** Tiền do `compute_compensation` tính từ order row và policy hiện hành; worker chỉ cung cấp dữ kiện. Model chỉ được gọi cho `plan` và `draft`, prompt không chứa ticket, không ảnh hưởng số tiền.
- **Truyền quote đầy đủ vào `issue_refund`.** Host tự trừ phần đơn đã được hoàn (T13, T14). Nếu shape trừ trước, T14 bị trừ hai lần.
- **Trace chỉ ghi dữ liệu đã qua allowlist:** `{claim_id, has_order_id}`, handoff đã sanitize, order view (7 field `ORDER_FIELDS`), tóm tắt lịch sử hoàn tiền, quote, phản hồi của host. Cố ý **không** ghi ticket (có thể chứa PII), dòng claim (có `parent_secret`, header), dòng order thô (có SĐT, địa chỉ, ghi chú nội bộ, tên hàng).
- **Crash:** bắt `InjectedCrash` chỉ để ghi event `crash` và flush trace, sau đó `raise` lại để T12 thấy crash thật.

## 4. Bằng chứng

- Ma trận student: `python -m pytest -q -m student -o addopts= -k orchestrator` → **62 passed** (T01–T10, T13, T14 × 5 seed; T11 gọi lại cùng claim; T12 crash `after_effect_before_checkpoint` rồi resume, vẫn 1 dòng ledger).
- Cổng host: `python -m pytest -q` → **64 passed** (54 test có sẵn + 10 test mới).
- Quét 62 file trace `traces/R-orchestrator-*` sinh ra từ ma trận: 0 file chứa `CANARY_SECRET_*` hoặc PII.
- Kiểm tra ngược test: sửa tạm orchestrator (trên bản sao) cho ghi nguyên dòng claim và dòng order vào trace → cả 5 test quét trace đều đỏ. Test bắt được lỗi lộ dữ liệu thật.
- Ablation R1 (`src/reports/ablation_r1.json`, lệnh trong research card), 14 claim × 5 seed:

  | Shape | Pass rate | Pass^5 | Cost/success (VND mô phỏng) | Model calls TB | Tool calls TB |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | workflow | 1.000 | 1.000 | 28.79 | 1.00 | 2.79 |
  | orchestrator | 1.000 | 1.000 | 56.88 | 1.86 | 5.57 |
  | swarm | 0.986 | 0.929 | 49.57 | 3.00 | 4.66 |

- Run id ví dụ: `R-orchestrator-C-014-s55` (T14, ledger 120.000 sau khi host trừ 30.000 đã hoàn), `R-orchestrator-C-002-s55` (`denied`, cùng trial mà `R-swarm-C-002-s55` fail).

## 5. Công cụ AI đã dùng

- **Claude Code (trong VS Code).** Dùng để: đọc repo và tóm tắt contract (`docs/contracts.md`, `business_rules.md`, `handoff.py`, `runtime.py`, `durability.py`); đề xuất cách chia việc cho 4 người; viết orchestrator theo từng bước 1–4; soạn file test; tra nguồn paper (arXiv:2512.08296) và soạn nháp research card.
- **Cách tự kiểm tra:**
  - Làm theo từng bước nhỏ, sau mỗi bước chạy lại cổng host và ma trận student để thấy số test xanh tăng đúng dự kiến (bước 2: 5 passed là C-004; bước 3: 10 passed thêm C-005; bước 4: 62 passed).
  - Mở trực tiếp trace (`traces/R-orchestrator-C-001-s11.json`) để đọc từng event, xác nhận không có ticket, dòng claim hay dòng order thô.
  - Đối chiếu mỗi nhánh `status` với bảng output contract trong `docs/contracts.md`.
  - Số liệu trong research card lấy từ file do `lab8.benchmark` sinh ra; không sửa tay JSON. Nguồn paper được tra lại trên arXiv và blog Google Research trước khi ghi CLAIM.
- Không dùng AI để bịa số liệu benchmark, run id hay commit hash.

## 6. Tự đánh giá

- **Làm tốt:** shape C qua đủ 62/62 test student và giữ cổng host xanh; ranh giới bảo mật được kiểm bằng test có thể đỏ thật, không chỉ dựa vào đọc code; ablation trả lời được câu hỏi R1 bằng số đo trên cùng claim, seed, giá.
- **Hạn chế:** orchestrator tốn gần gấp đôi workflow (cost/success 56.88 so với 28.79) mà không tăng pass rate trên public; investigator hiện chạy tuần tự nên chưa khai thác được phần đọc độc lập có thể song song. Kết quả mới đo trên 14 claim public, chưa có số trên bộ hidden 40 claim. MockLLM cố định nên hiện tượng khuếch đại lỗi giữa các agent không xuất hiện.
- **Nếu làm tiếp:** thử bonus B1 (investigator song song với mô hình latency mô phỏng) để đo xem critical path giảm được bao nhiêu trên một task chủ yếu tuần tự.
