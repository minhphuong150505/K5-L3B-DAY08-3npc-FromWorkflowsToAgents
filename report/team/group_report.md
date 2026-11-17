# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: 3npc
- Lớp: L3B
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): 8f0cf8c
- Repo: https://github.com/minhphuong150505/K5-L3B-DAY08-3npc-FromWorkflowsToAgents, nhánh `main`
- Slide demo: _(P2 điền link)_

## 2. Mục tiêu và cách tiếp cận

**Bài toán.** Nhóm xử lý claim hoàn phí vận chuyển của LogiX-VN bằng bốn kiến trúc có cùng chữ ký `run_claim`, rồi chọn kiến trúc **ít tự chủ nhất mà vẫn làm được việc** dựa trên số đo. Ranh giới nhóm giữ xuyên suốt: số tiền, approval và chống ghi trùng do **code** quyết. Model chỉ đọc và soạn chữ. Chữ trong ticket là dữ liệu của khách, không phải lệnh.

**Chia việc.** Nhóm 4 người, mỗi người làm trên một nhánh riêng, mở PR vào `main`, và trưởng nhóm merge:

| Người | Vai | Nhánh / PR |
| --- | --- | --- |
| P1 `minhphuong150505` | Workflow, integration, benchmark, ADR | `feat/workflow` (PR #1), `feat/cp5-benchmark` (PR #5) |
| P2 `tranha1764` | Single agent, slide | `feat/single` (PR #3) |
| P3 `hungdt31` | Orchestrator, handoff, research card | `feat/orchestrator` (PR #4) |
| P4 `ngominhcuong` | Ledger, crash, evaluation, số liệu slide | `feat/eval` |

**Thứ tự làm:**

1. Đọc `swarm_reference.py`, `durability.py`, `handoff.py`, `runtime.py` và hai file docs về luật nghiệp vụ, contract.
2. Viết shape A workflow trước, vì đây là mốc tất định để so với các shape khác.
3. Viết song song shape B single và shape C orchestrator.
4. Ở CP3, truyền `crash_at` vào `issue_refund` và sanitize handoff.
5. Ở CP5, chạy benchmark 4 shape × 5 seed, crash suite, ablation R1 và tự kiểm trên bộ hidden.

## 3. Giải pháp

Cả ba shape dùng chung các cửa của host:

- Đọc claim qua `get_claim_view` (không `SELECT *`, nên không bao giờ chạm tới `parent_secret` hay `raw_headers`).
- Đọc đơn qua `lookup_order`, chỉ thấy đơn của đúng khách gửi claim và chỉ trả các field trong `ORDER_FIELDS`.
- Tính tiền **chỉ** bằng `compute_compensation` từ dòng order.
- Ghi tiền **chỉ** qua `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`.

Shape không tự trừ phần đã hoàn trước đó, vì host tự trừ theo trần của đơn (T13, T14). Mọi nhánh return đều đi qua `finish()`, nên trace luôn được ghi và có `run_id` trùng `RunResult`. Khi có `InjectedCrash`, shape chỉ ghi trace rồi `raise` lại ngay. Lần chạy lại sau đó đi qua idempotency key `refund:{claim_id}`, nên vẫn chỉ có một refund.

| | A `workflow` | B `single` | C `orchestrator` |
| --- | --- | --- | --- |
| Cách điều khiển | Các bước Python cố định | Vòng `run_react`, tối đa 8 bước; `decide` chỉ chọn tool đọc (`get_claim_view` → `lookup_order` → `compute_compensation`) | Orchestrator gọi model `plan`, dựng handoff, rồi giao cho investigator chỉ đọc |
| Model làm gì | Chỉ soạn câu trả lời (`draft`) | Chỉ soạn câu trả lời; vòng lặp không được gọi `issue_refund` | `plan` và `draft`; prompt không chứa ticket, model không quyết số tiền |
| Ai tính tiền / ai ghi | Code của shape / `issue_refund` | Code sau vòng lặp / `issue_refund` | Orchestrator, từ order view mà investigator trả về / `issue_refund` |
| Handoff | Không có | Không có | `make_handoff(facts={}, allowed_tools=[lookup_order, lookup_refund_history, lookup_policy])`. Handoff dựng bằng allowlist trong code, không phải bằng một bản tóm tắt của LLM |

**Trace ghi các event sau:**
- Workflow và single: `step` (`found`, `has_order_id`, `visible`, `reason`), `quote` (`amount_vnd`, `reason`, `clause_ids`), `issue_refund` (`ok`, `reason`, `conflict`), `crash`, `decision`.
- Orchestrator: ghi thêm `claim`, `handoff` đã sanitize, và `investigator` (order view đã qua allowlist cùng tóm tắt lịch sử refund).

**Trace cố ý không ghi:** claim row, nội dung ticket, order row thô (SĐT, địa chỉ, tên hàng, ghi chú nội bộ), `parent_secret` và header.

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

**Bộ public:** 14 claim × 5 seed (11, 22, 33, 44, 55), cùng `config/pricing.yaml`, MockLLM, và mỗi trial chạy trên một SQLite mới. Nguồn: `src/reports/benchmark.json`.

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Steps TB | Steps p95 |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.79 | 4.43 | 5 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.79 | 4.43 | 5 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.88 | 5.36 | 6 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 | 3 |

- **Swarm sai đúng 1/70 trial (`R-swarm-C-002-s55`):** ở seed 55, swarm tin "trễ 5 ngày" trong ticket thay vì `delay_days` = 2 của order, nên refund 20.000 VND trong khi đáng lẽ phải từ chối. Workflow, single và orchestrator đều từ chối đúng claim này ở cả 5 seed.
- **Crash safety:** 20/20 (`src/reports/crash.json`).
- **Tự kiểm hidden:** 40 claim × 5 seed trên `student_drop/` (`src/reports/hidden_selfcheck.json`), mỗi shape 200 trial, không có `error` và không có `leak_suspect`. Phân bố status của cả 3 shape giống hệt nhau: resolved 90, denied 95, escalated 10, needs_info 5. Bộ này không có nhãn nên không ra pass rate; điểm hidden chính thức do grader của giảng viên chấm.
- **Cổng host:** `python -m pytest -q` ra 137 passed.
- **Ma trận student:** `python -m pytest -q -m student -o addopts=` ra 248 passed (mỗi shape 62/62).
- **`check_submission`:** 0 FAIL.

**Ablation R1** (`src/reports/ablation_r1.json`, 210 trial): thêm tầng orchestrator và investigator (workflow → orchestrator) không đổi pass rate, nhưng cost/success tăng 1,98× (56.88 so với 28.79). Kết quả này khớp với hypothesis trong research card.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md` (nhóm chọn **workflow**). Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- **Thiếu thành viên lúc chia việc:** khi chia việc, repo mới có 3 collaborator; thành viên thứ tư còn lời mời đang chờ. Nhóm vẫn chia việc cho đủ 4 người và chờ bạn ấy accept.
- **Lịch lab đổi:** lịch đổi sang 9:00–13:00, nên nhóm cập nhật lại mốc checkpoint trong `TEAM.md`, và phần demo chuyển sang chỉ dùng slide.
- **Crash suite có sẵn chỉ chạy swarm:** `lab8.crash_test` chỉ chạy shape swarm. Để kiểm crash cho shape của nhóm, mỗi shape có test crash rồi chạy lại riêng (ví dụ `test_workflow_crash_then_resume_keeps_one_refund` chạy cả 3 điểm crash). Ngoài ra nhóm tự chạy thêm 14 claim × 3 điểm crash × 2 seed cho từng shape: cả 3 shape đều 84/84, không lần nào có quá 1 refund.
- **Thiếu file ablation:** `research_card.md` dẫn tới `src/reports/ablation_r1.json`, nhưng file chưa được commit. Nhóm sinh lại bằng đúng lệnh ghi trong research card và kiểm số khớp trước khi commit.
- _(P2, P3, P4 bổ sung lỗi mình gặp, kèm lệnh và output)_

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

- **MockLLM không phải model sản xuất,** và latency là `unavailable`. Cost là giá token mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API.
- **Ba shape đúng như nhau vì mọi quyết định có hệ quả đều nằm trong code.** Quote, approval và ghi ledger do code giữ; `decide` của single cũng là code tất định. Vì vậy benchmark này chưa đo được lợi ích hay rủi ro thật của việc để model tự chọn bước. Single và workflow ra số giống hệt nhau cũng vì lý do này.
- **Corpus public chỉ có 14 claim,** và bộ hidden tự kiểm không có nhãn.
- **Kết luận chọn workflow sẽ đổi nếu:**
  - Grader hidden cho thấy workflow dưới 0.75 ở loại claim mà agent đọc thêm nguồn bắt được.
  - Mỗi claim cần nhiều nguồn chứng cứ độc lập chạy song song được, và latency được đo thật.
  - Model thật thay MockLLM, và việc hiểu ticket thực sự ảnh hưởng tới kết quả.

## 8. Tài liệu tham khảo

- Google Research 2026, *Towards a Science of Scaling Agent Systems* (R1 trong `report/team/research_card.md`).
- Đề bài và tài liệu trong repo: `README.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
- Công cụ AI: Claude Code hỗ trợ đọc repo, viết shape workflow và test, soạn báo cáo. Nhóm tự chạy lại toàn bộ lệnh để kiểm số liệu. Chi tiết nằm trong báo cáo cá nhân.
