# Báo cáo cá nhân — 2A202603997_NguyenMinhPhuong

## 1. Thông tin thành viên

- Họ tên: Nguyễn Minh Phương
- MSSV: 2A202603997
- Email: 26ai.phuongnm3@vinai.edu.vn
- GitHub: `minhphuong150505`

## 2. Phần việc phụ trách

Vai **P1 — Trưởng nhóm: Workflow + Integration** (xem bảng phân công trong `TEAM.md`).

- Shape A `workflow`: `src/lab8/shapes/workflow.py`.
- Test bổ sung cho shape A: `src/tests/test_workflow_extra.py`.
- Phân công công việc cho 4 thành viên và quản lý repo nhóm: tạo nhánh, review và merge PR vào `main`, giữ cổng host `python -m pytest -q` luôn xanh.

## 3. Đóng góp cụ thể

### Commit chính

| Hash | Nội dung |
| --- | --- |
| `eef4d00` | `feat(workflow)`: cài shape A và thêm `test_workflow_extra.py` (merge vào `main` qua PR #1, merge commit `ee21496`) |
| `c6fee68` | Đưa bảng phân công 4 người vào `TEAM.md` |
| `de98c59`, `a24da90` | Chỉnh phân công (demo chỉ dùng slide) và đổi lịch checkpoint sang 9:00–13:00 |
| `8f0cf8c` | Commit chốt đầu tiên: thêm `src/reports/benchmark.json` (4 shape × 14 claim × 5 seed), `crash.json` (20/20), `hidden_selfcheck.json` (PR #5) |
| `f15bd04` | Điền `decision_adr.md`: chọn `workflow`, commit hash, run id, số liệu (PR #5) |

### Shape A — các bước và lý do

1. Đọc claim qua `get_claim_view` (không `SELECT *`), để `parent_secret` và `raw_headers` không bao giờ vào bộ nhớ của shape.
2. Thiếu `order_id` → `needs_info`, không ghi ledger.
3. `lookup_order` theo `principal_id` của claim. Không thấy đơn (không tồn tại hoặc của khách khác) → `escalated`. Hàm này chỉ trả các field trong `ORDER_FIELDS`, nên không có SĐT, địa chỉ hay ghi chú nội bộ.
4. Tính tiền **chỉ** bằng `compute_compensation` từ dòng order. Số ngày trễ khách ghi trong ticket bị bỏ qua hoàn toàn. Workflow không copy khối `REFERENCE_WEAKNESS` của swarm.
5. Quote = 0 → `denied`, không gọi `issue_refund`.
6. Quote > 0 → `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`. Shape không tự trừ phần đã hoàn trước đó, vì host tự trừ. Nếu shape cũng trừ thì bị trừ hai lần (T13, T14).
7. Host từ chối → `denied`, host tự ghi audit `policy_denied`. Lệch số tiền (`conflict`) → `failed`. Thành công → `resolved`.
8. MockLLM chỉ được gọi để soạn câu trả lời (`purpose="draft"`). Model không chọn số tiền và không ghi refund.

### Quyết định kỹ thuật

- **Không nuốt `InjectedCrash`:** chỉ bắt lỗi để ghi trace rồi `raise` lại ngay. Nhờ vậy, lần chạy lại trên cùng DB đi qua idempotency key `refund:{claim_id}` và vẫn chỉ có 1 refund.
- **Trace chỉ ghi field đã qua allowlist:** tên bước, `visible`/`reason`, quote (`amount_vnd`, `reason`, `clause_ids`), kết quả `issue_refund`. Trace cố ý **không** ghi nội dung ticket, claim row, order row, `parent_secret` hay header.
- **Mọi nhánh return đều đi qua `finish()`**, kể cả `needs_info`, `escalated` và `unknown_claim`. Vì vậy trace luôn được ghi, có `run_id` trùng `RunResult`, và `refund_effects`/`committed_audit_count` lấy thẳng từ ledger chứ không điền tay.

### CP5 — Benchmark, ADR và kiểm tra bài nộp

- Chạy benchmark 4 shape × 5 seed trên bộ public:

  | Shape | Pass | pass^5 | Variance | Cost/success (VND) |
  | --- | ---: | ---: | ---: | ---: |
  | workflow | 1.000 | 1.000 | 0 | 28.79 |
  | single | 1.000 | 1.000 | 0 | 28.79 |
  | orchestrator | 1.000 | 1.000 | 0 | 56.88 |
  | swarm | 0.986 | 0.929 | 0.000816 | 49.57 |

- Chạy crash suite: 20/20.
- Tự kiểm trên `student_drop/` (40 claim × 5 seed): cả 3 shape không có trial `error` hay `leak_suspect`. Mình chỉ dùng `student_drop/` (không nhãn) như README hướng dẫn, không dùng file nhãn hidden.
- Viết ADR chọn **workflow**: shape ít tự chủ nhất, đạt pass cao nhất với chi phí thấp nhất. Swarm sai `R-swarm-C-002-s55` vì tin số ngày trễ trong ticket. Orchestrator đúng như workflow nhưng tốn gần gấp đôi.
- Làm đúng thứ tự trong `SUBMISSION.md`: commit report trước (`8f0cf8c`), ghi hash đó vào ADR, rồi commit ADR. Khi cả nhóm đã merge xong test, báo cáo và trang demo, mình chạy lại toàn bộ report (số liệu không đổi) và chốt lại ở commit `7a3eb61` để commit được chấm chứa đủ đóng góp của 4 người. `python -m lab8.check_submission` ra **0 FAIL, 0 WARN**.
- Rà lại repo trước khi nộp và phát hiện `src/reports/ablation_r1.json` (research card dẫn tới) chưa được commit. Mình sinh lại bằng đúng lệnh ghi trong research card (210 trial, số khớp) rồi commit.
- Soạn `group_report.md` với số liệu lấy từ `src/reports/`, và điền phần Thông tin nhóm trong `TEAM.md`.

### Test đã thêm (`src/tests/test_workflow_extra.py`, chạy trong cổng host)

| Test | Kiểm tra gì |
| --- | --- |
| `test_workflow_ignores_delay_written_in_ticket` | C-002 (ticket ghi "trễ 5 ngày", đơn trễ 2 ngày) → `denied`, 0 refund ở cả 5 seed, kể cả seed 55 là seed swarm làm sai |
| `test_workflow_amount_comes_from_compute_compensation` | Với cả 14 claim public, claim nào `resolved` thì số tiền đúng bằng `compute_compensation` |
| `test_workflow_trace_has_no_secret_or_ticket_text` | Trace của 14 claim đúng contract v1, không có `CANARY_SECRET`, `Bearer` hay nội dung ticket; `RunResult` cũng không có secret |
| `test_workflow_crash_then_resume_keeps_one_refund` | Crash ở cả 3 điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) rồi chạy lại C-012 → `resolved` 35.000 VND, 1 dòng ledger, 1 audit `refund_committed` |

## 4. Bằng chứng

- Commit `eef4d00`, PR #1: https://github.com/minhphuong150505/K5-L3B-DAY08-3npc-FromWorkflowsToAgents/pull/1
- Kết quả chạy trên máy (Linux, Python 3.12), trong `src/`:

```text
$ python -m pytest -q -m student -o addopts= -k workflow
62 passed, 276 deselected

$ python -m pytest -q
90 passed, 248 deselected          # trước khi thêm test: 54 passed

$ python -m lab8.crash_test --count 20 --out <thư mục tạm>
crash_safety 20/20
```

- PR #5 (CP5): https://github.com/minhphuong150505/K5-L3B-DAY08-3npc-FromWorkflowsToAgents/pull/5 — `src/reports/benchmark.json`, `crash.json`, `hidden_selfcheck.json`, `ablation_r1.json`, `report/team/decision_adr.md`
- Run id mẫu của shape A: `R-workflow-C-002-s55`, `R-workflow-C-012-s11` (dạng `R-workflow-<claim_id>-s<seed>`).

## 5. Công cụ AI đã dùng

| Công cụ | Dùng vào việc gì |
| --- | --- |
| Claude Code | Đọc source và docs của repo (`swarm_reference.py`, `durability.py`, `tools.py`, `docs/contracts.md`), đếm collaborator, rồi soạn bảng phân công cho 4 người |
| Claude Code | Viết `workflow.py` theo 8 bước trong docstring và viết `test_workflow_extra.py` |
| Claude Code | Chạy benchmark, crash suite, tự kiểm hidden; soạn ADR và `group_report.md` từ số trong `src/reports/` |
| Claude Code | Soạn nháp báo cáo cá nhân này |

**Cách tự kiểm tra:**

- Tự đọc lại `workflow.py`, đối chiếu từng bước với docstring và [docs/contracts.md](../../docs/contracts.md): tiền chỉ do `compute_compensation` tính, quote đầy đủ được truyền vào `issue_refund`, `InjectedCrash` không bị nuốt, trace không chứa ticket/secret.
- Tự chạy ma trận student của workflow (62/62), cổng host (90 passed) và crash suite (20/20) như ở mục 4.
- Không dùng AI để bịa số liệu: mọi con số trong báo cáo này là output của lệnh đã chạy.

## 6. Tự đánh giá

> Nháp do Claude Code soạn dựa trên kết quả thực tế; mình sẽ sửa lại cho đúng trải nghiệm của mình.

**Làm tốt:**

- Shape A xong sớm và qua đủ 62/62 test public ngay lần chạy đầu. Shape không đi qua model ở bước tính tiền, nên kết quả không đổi theo seed: đây là lựa chọn ít tự chủ nhất, dùng làm mốc để so với B, C, D.
- Test bổ sung khóa lại ba must-pass ở mức shape A: không tin ticket, không lộ secret trong trace, crash không tạo refund thứ hai.
- Phân công rõ từng file, từng test và từng mốc checkpoint cho 4 người, nên các thành viên làm song song trên nhánh riêng mà không đụng file của nhau.

**Khó khăn và cách xử lý:**

- Lúc chia việc, repo mới có 3 collaborator đã nhận lời mời; thành viên thứ tư (`ngominhcuong`) còn lời mời đang chờ accept.
- Phải hiểu vì sao **không** được tự trừ phần đã hoàn (T13, T14) và vì sao không được bắt `InjectedCrash`. Mình xử lý bằng cách đọc `durability.issue_refund` và viết test crash/resume riêng để chứng minh.
- Lịch lab đổi sang 9:00–13:00 và phần demo chuyển sang chỉ dùng slide, nên mình cập nhật lại bảng phân công trong `TEAM.md`.

**Cần cải thiện:**

- Viết thêm test cho các nhánh `escalated` (đơn của khách khác) và `failed` (lệch số tiền).
