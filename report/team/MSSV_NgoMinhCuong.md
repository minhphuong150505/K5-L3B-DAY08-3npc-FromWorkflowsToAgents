# Báo cáo cá nhân — [MSSV]\_NgoMinhCuong

## 1. Thông tin thành viên

- Họ tên: Ngô Minh Cương
- MSSV: 2A202603954
- Email: 26ai.cuongnm5@vinai.edu.vn
- GitHub: `ngominhcuong`

## 2. Phần việc phụ trách

Vai **P4 — Ledger / Crash / Evaluation + Trang HTML demo** (xem bảng phân công trong `TEAM.md`).

- Kiểm thử chéo ma trận public T01–T14 và cổng host cho cả 3 shape (`workflow`, `single`, `orchestrator`).
- Test bổ sung về durability / crash-resume: `src/tests/test_crash_resume_extra.py`.
- Sinh bằng chứng crash 20/20 (`src/reports/crash.json`), tự kiểm trên `student_drop/` (`src/reports/hidden_selfcheck.json`), chạy benchmark (`src/reports/benchmark.json`) và rà bảo mật trace trong `src/traces/`.
- Xây dựng trang HTML demo tương tác (`demo/index.html`) và kịch bản thuyết trình (`demo/demo_script.md`).

## 3. Đóng góp cụ thể

### Commit chính

| Hash      | Nội dung                                                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `85d947c` | `feat(eval)`: thêm `src/tests/test_crash_resume_extra.py` và `src/reports/crash.json` (`20/20`)                                                        |
| `2594516` | `feat`: thêm `demo/index.html`, `src/reports/benchmark.json`, `src/reports/hidden_selfcheck.json` (merge vào `main` qua PR #7, merge commit `4b91210`) |

### Kiểm thử & Đánh giá (Evaluation)

1. **Kiểm thử chéo ma trận public & cổng host:**
   - Cài đặt `.venv` trong `src/`, chạy `python -m pytest -q` (`137 passed`) và `python -m pytest -q -m student -o addopts=` (`248 passed` — toàn bộ 62 test × 4 shape đều xanh).
2. **Kiểm tra Crash & Idempotency (`test_crash_resume_extra.py`):**
   - Bổ sung 9 test case kiểm tra cả 3 shape nhóm viết (`workflow`, `single`, `orchestrator`) × 3 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) trên claim `C-012`.
   - Xác nhận `InjectedCrash` được ném ra đúng (không bị nuốt), và sau khi resume trên cùng SQLite chỉ có đúng **1 dòng `refund_ledger`** và **1 audit `refund_committed`**.
3. **Crash suite 20 điểm & rà bảo mật trace:**
   - Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json` đạt `20/20`.
   - Rà thư mục `src/traces/*.json` bằng `Select-String` với các mẫu `CANARY_SECRET|CANARY_INTERNAL|parent_secret|raw_headers`: không phát hiện rò rỉ.
4. **Tự kiểm hidden (`student_drop/`) & Benchmark public:**
   - Chạy tự kiểm 40 claim × 5 seed trên `student_drop/` cho cả 3 shape (`src/reports/hidden_selfcheck.json`): mỗi shape 200 trial, `error_trials = 0`, `leak_suspect_trials = 0`.
   - Chạy `lab8.benchmark` trên bộ public 14 claim × 5 seed (`src/reports/benchmark.json`): `workflow` và `single` đạt `1.000` (`cost/success = 28.79 VND`, `variance = 0`), `orchestrator` đạt `1.000` (`56.88 VND`), `swarm` đạt `0.986` (`pass^5 = 0.929`, sai 1 trial `C-002` seed 55).
5. **Trang HTML demo (`demo/index.html`) & kịch bản (`demo/demo_script.md`):**
   - Thiết kế trang HTML tĩnh 1 file (mở trực tiếp bằng trình duyệt, không cần server) trình bày 10 phần: bài toán, thang tự chủ A–D, ranh giới code/model, mô phỏng từng bước workflow (T01/T02/T13/T14), mô phỏng crash-resume, bảo mật allowlist, biểu đồ benchmark + heatmap theo seed, trace thật `C-002` seed 55 đã sanitize và ADR.

### Test đã thêm (`src/tests/test_crash_resume_extra.py`, chạy trong cổng host)

| Test                                                                                                 | Kiểm tra gì                                                                                                                                                                                                                                       |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_crash_and_resume_keeps_single_refund_and_audit` (parametrize 3 shape × 3 điểm crash = 9 cases) | Crash tại `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint` trên `workflow`, `single`, `orchestrator` → ném `InjectedCrash` → resume trên cùng DB trả `resolved`, đúng 1 dòng `refund_ledger` và `committed_audit_count == 1` |

## 4. Bằng chứng

- PR #7 (`feat/eval-demo`): https://github.com/minhphuong150505/K5-L3B-DAY08-3npc-FromWorkflowsToAgents/pull/7 (commits `85d947c`, `2594516`, merge `4b91210`).
- Kết quả chạy trên máy (Windows, Python 3.11), trong `src/`:

```text
$ python -m pytest -q
137 passed, 248 deselected    # (trước khi thêm 9 test crash/resume; sau khi thêm: 146 passed)

$ python -m pytest -q -m student -o addopts=
248 passed, 137 deselected

$ python -m lab8.crash_test --count 20 --out reports/crash.json
crash_safety: 20/20

$ python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --out reports/hidden_selfcheck.json
200 trials/shape: error_trials=0, leak_suspect_trials=0

$ python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
workflow: 1.000 | single: 1.000 | orchestrator: 1.000 | swarm: 0.986
```

- Trang demo: `demo/index.html` và kịch bản thuyết trình `demo/demo_script.md`.

## 5. Công cụ AI đã dùng

| Công cụ                    | Dùng vào việc gì                                                                                                            |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Antigravity (AI assistant) | Giải thích cấu trúc repo, các mốc checkpoint CP1–CP5 và vai trò P4 (`durability.py`, `contracts.md`, `metrics.md`)          |
| Antigravity                | Hỗ trợ viết `src/tests/test_crash_resume_extra.py` kiểm tra 3 điểm crash trên 3 shape                                       |
| Antigravity                | Thiết kế `demo/index.html` (giao diện tương tác, biểu đồ benchmark, trace viewer đã sanitize) và soạn `demo/demo_script.md` |
| Antigravity                | Soạn nháp báo cáo cá nhân này dựa trên commit và output thực tế                                                             |

**Cách tự kiểm tra:**

- Tự cài `.venv`, chạy trực tiếp `pytest -q`, `pytest -q -m student -o addopts=`, `lab8.crash_test`, `lab8.benchmark` trên bộ public và `student_drop/`.
- Tự chạy `Select-String` rà `src/traces/*.json` và kiểm tra dữ liệu nhúng trong `demo/index.html` để đảm bảo không chứa `CANARY_SECRET_*`, SĐT, địa chỉ hay ghi chú nội bộ.
- Mọi số liệu trong báo cáo và trang demo đều đối chiếu trực tiếp từ `src/reports/benchmark.json`, `src/reports/crash.json` và `src/reports/hidden_selfcheck.json`, không bịa số liệu.

## 6. Tự đánh giá

**Làm tốt:**

- Hoàn thành đầy đủ kiểm thử chéo, bổ sung 9 test crash/resume bao phủ cả 3 shape và sinh đủ các file bằng chứng (`crash.json`, `hidden_selfcheck.json`, `benchmark.json`).
- Xây dựng trang HTML demo trực quan giúp người xem dễ hình dung sự khác biệt giữa `workflow` và `swarm` (đặc biệt qua trace `C-002` seed 55 và mô phỏng điểm crash `after_effect_before_checkpoint`).

**Khó khăn và cách xử lý:**

- Ban đầu chưa accept lời mời collaborator trên GitHub và chưa tạo `.venv` trong `src/` nên `pytest` báo `ModuleNotFoundError: No module named 'yaml'`. Đã accept lời mời, tạo `.venv`, cài `requirements.txt` và chạy xanh toàn bộ test.
- Cần cẩn thận không commit nhầm thư mục `student_drop/`, `traces/` hay file `*.sqlite` khi đẩy nhánh `feat/eval-demo`.

**Cần cải thiện:**

- Có thể bổ sung thêm test tự động cho trường hợp `amount_conflict` (gọi lại với số tiền khác) trên cả 3 shape chứ không chỉ ở mức `durability.issue_refund`.
