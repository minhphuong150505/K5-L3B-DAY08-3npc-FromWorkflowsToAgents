# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

...

### 3.3 Shape C — Orchestrator (Đoàn Trí Hùng)

File: `src/lab8/shapes/orchestrator.py`. Orchestrator giữ mọi quyết định có hệ quả (tiền, trạng thái, ghi refund). Investigator chỉ đi đọc dữ kiện, nhận việc qua handoff `handoff.v1` và không có tool ghi.

**Luồng xử lý**

```text
orchestrator                         investigator (chỉ đọc)              host
------------                         ----------------------              ----
get_claim_view ── không có → failed (unknown_claim)
   │            ── thiếu order_id → needs_info
model "plan"
make_handoff(facts={}, tools đọc) ──▶ lookup_order (theo principal của claim)
                                      lookup_refund_history
                                      lookup_policy
   ◀── order view (7 field allowlist) ──┘
order không visible → escalated
compute_compensation(order row)
model "draft"
quote = 0 → denied (không gọi host)
quote > 0 ─────────────────────────────────────────────────────────▶ issue_refund(quote đầy đủ, crash_at)
   ◀── ok → resolved · từ chối → denied · amount_conflict → failed ──┘
```

**Ranh giới code / model**

| Việc | Ai quyết trong shape C |
| --- | --- |
| Claim có tồn tại, có `order_id` không | Code (orchestrator) |
| Đơn có thuộc principal của claim không | Code (`lookup_order` của investigator) |
| Số tiền quote | Code: `compute_compensation` trên order row và policy hiện hành; số ngày trễ trong ticket bị bỏ qua |
| Approval, trần theo đơn, idempotency, ghi ledger | Host (`durability.issue_refund`); orchestrator là shape duy nhất gọi cửa này |
| Lập kế hoạch giao việc, soạn câu trả lời | Model (MockLLM `plan`, `draft`); prompt không chứa ticket, kết quả không ảnh hưởng số tiền |

Orchestrator tự quote từ order view mà investigator trả về, không nhận số tiền từ worker. Quote truyền vào host là **quote đầy đủ**; host tự trừ phần đơn đã được hoàn (T13, T14). Khi có `crash_at`, shape chuyển nguyên cho host và để `InjectedCrash` thoát ra sau khi ghi trace (T12).

**Handoff được sanitize thế nào**

- Dựng bằng `lab8.handoff.make_handoff`, tức là allowlist viết bằng code, không phải tóm tắt bằng LLM. Chỉ còn 8 field: `contract_version`, `request_id`, `claim_id`, `principal_scope`, `task`, `facts`, `allowed_tools`, `max_output_tokens`.
- `facts={}`: lúc giao việc orchestrator chưa có dữ kiện nào đã kiểm chứng, nên không có gì từ ticket đi qua ranh giới. Investigator tự đọc order từ DB.
- `allowed_tools = [lookup_order, lookup_refund_history, lookup_policy]`. `make_handoff` từ chối mọi write tool (`issue_refund`, `append_audit`) bằng `HandoffError`; `sanitize` từ chối payload còn `CANARY_SECRET_`, `parent_secret` hay `raw_headers`. Không giao `get_clause` vì runtime không chạy tool này và clause cũ (`SHIP-LATE-OLD`) dễ bị dùng sai.
- Investigator chạy qua `run_readonly_investigators` với `worker=True`, nên dù handoff có sai thì runtime vẫn chặn tool ghi.

**Trace ghi những event nào**

| Event | Nội dung |
| --- | --- |
| `claim` | `claim_id`, `has_order_id` |
| `handoff` | Handoff đã sanitize (8 field allowlist) |
| `investigator` | Order view (7 field `ORDER_FIELDS`), `refund_count` / `refunded_vnd`, số policy hiện hành |
| `quote` | `amount_vnd`, `reason`, `clause_ids`, `parts` |
| `host` | `ok`, `reason`, `conflict` từ `issue_refund` |
| `crash` | Điểm crash (chỉ khi có `InjectedCrash`) |
| `decision` | `status`, `proposal_amount`, `reason` (mọi nhánh return đều có, qua `finish()`) |

Cố ý **không** ghi: ticket (chữ khách viết, có thể chứa PII), dòng claim thô (`parent_secret`, `raw_headers_json`), dòng order thô (`phone`, `address`, `internal_note`, `item_name`), parent context. Test `src/tests/test_orchestrator_handoff_extra.py` quét trace của 5 claim để bắt các chuỗi này; khi cố ý cho shape ghi dòng claim và dòng order thô, cả 5 test đều đỏ.

**Kết quả của shape C:** 62/62 test student (T01–T14, gồm T11 gọi lại và T12 crash rồi resume). So với workflow trên cùng 14 claim × 5 seed, pass rate bằng nhau (1.000) nhưng cost/success gần gấp đôi (56.88 so với 28.79 VND mô phỏng) vì thêm lời gọi `plan` và investigator đọc lại dữ kiện; chi tiết ở `report/team/research_card.md`.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

...

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
