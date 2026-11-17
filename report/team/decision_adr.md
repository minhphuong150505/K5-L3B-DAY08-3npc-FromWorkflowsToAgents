# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 2aae89e
- Run id dẫn chứng: R-workflow-C-002-s55 (pass, denied) so với R-swarm-C-002-s55 (fail, resolved != denied); R-workflow-C-013-s11 (đơn đã hoàn, denied), R-workflow-C-014-s55 (trần theo đơn, resolved) — src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (70 trial = 14 claim × 5 seed 11,22,33,44,55; src/reports/benchmark.json)
- Cost per success (mô phỏng, VND): 28.79 (tổng 2015.0 VND / 70 thành công; orchestrator 56.88, swarm 49.57)
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 trên public benchmark (70/70 trial reason `ok`, không trial `leak_suspect`, không refund ngoài nhãn); hidden self-check 200 trial: leak_suspect 0, error 0 (src/reports/hidden_selfcheck.json)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Bảng dưới lấy từ `src/reports/benchmark.json`, chạy bằng `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` tại commit `2aae89e`. Cả bốn shape dùng cùng corpus 14 claim, cùng 5 seed, cùng `config/pricing.yaml`, cùng MockLLM, và mỗi trial chạy trên một SQLite mới.

| Shape | Pass rate | pass^5 | Variance (min–max) | Cost/success (VND) | Model calls TB | Tool calls TB | Steps TB |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0 (1.000–1.000) | 28.79 | 1.00 | 2.79 | 4.43 |
| single | 1.000 | 1.000 | 0 (1.000–1.000) | 28.79 | 1.00 | 2.79 | 4.43 |
| orchestrator | 1.000 | 1.000 | 0 (1.000–1.000) | 56.88 | 1.86 | 5.57 | 5.36 |
| swarm | 0.986 | 0.929 | 0.000816 (0.929–1.000) | 49.57 | 3.00 | 4.66 | 2.80 |

- **Ba shape của nhóm:** workflow, single và orchestrator đều đạt pass rate 1.000 và không dao động theo seed.
- **Swarm sai đúng một trial (`R-swarm-C-002-s55`):** ở seed 55, swarm tin số ngày trễ khách ghi trong ticket ("trễ 5 ngày") thay vì `delay_days` = 2 của order. Kết quả là refund 20.000 VND trong khi đáng lẽ phải từ chối.
- **Workflow so với single:** hai shape hòa nhau trên mọi chỉ số, nhưng workflow ít tự chủ hơn. Workflow không có vòng ReAct, thứ tự bước cố định trong code, và model chỉ soạn câu trả lời.
- **Workflow so với orchestrator:** orchestrator cũng đúng hết, nhưng tốn gần gấp đôi (56.88 so với 28.79 VND mỗi lần thành công) vì thêm lời gọi model và đọc lại tool qua investigator.

Vì vậy nhóm chọn **workflow**: đây là kiến trúc ít tự chủ nhất, mà vẫn đạt pass rate cao nhất với chi phí thấp nhất.

## Có đáng đổi lấy multi-agent không

Không, trên dữ liệu hiện có. Multi-agent không tăng pass rate: orchestrator chỉ bằng workflow, còn swarm thấp hơn và có variance > 0. Trong khi đó, cost/success của hai shape này cao hơn workflow 1,7–2,0 lần. Claims flow là một chuỗi tuần tự (claim → order → quote → refund), bước sau phụ thuộc bước trước, nên không có phần việc độc lập nào để chia cho nhiều agent.

Quyết định sẽ đảo lại nếu:

- Bộ hidden cho thấy workflow dưới ngưỡng 0.75 ở loại claim mà một agent đọc thêm nguồn (ví dụ `get_clause`, lịch sử refund) bắt được, còn các bước cố định thì bỏ sót.
- Mỗi claim cần nhiều nguồn chứng cứ độc lập, đọc song song được, và latency được đo thật. Khi đó chạy investigator song song có thể rút ngắn critical path.
- Model thật thay MockLLM, và việc hiểu ticket (ngôn ngữ tự nhiên, nhiều ý) thực sự ảnh hưởng tới kết quả, chứ không chỉ để soạn câu trả lời.

## Trace và bằng chứng

Trace của workflow ghi các event sau:

- `step`: với `get_claim_view` ghi `found`, `has_order_id`; với `lookup_order` ghi `visible`, `reason`.
- `quote`: `amount_vnd`, `reason`, `clause_ids`.
- `issue_refund`: `ok`, `reason`, `conflict`.
- `crash`: `at`, chỉ khi có crash.
- `decision`: `status`, `proposal_amount`, `reason`.

Mọi nhánh return, kể cả `needs_info`, `escalated` và `unknown_claim`, đều ghi trace qua `finish()`. Nhờ vậy trace luôn tồn tại và có `run_id` trùng với `RunResult`.

Trace cố ý **không** ghi các thứ sau:

- **Claim row thô**, vì có `parent_secret` và `raw_headers`. Shape chỉ đọc claim qua `get_claim_view`, không dùng `SELECT *`.
- **Nội dung ticket**, vì đây là chữ của khách, có thể chứa PII hoặc câu injection. Ticket là dữ liệu chứ không phải lệnh, và quote không dựa vào ticket.
- **Order row thô**, vì có SĐT, địa chỉ, tên hàng và ghi chú nội bộ. `lookup_order` chỉ trả các field trong `ORDER_FIELDS`, và trace chỉ ghi `visible`/`reason`.

Trace nằm ở `traces/<run_id>.json`, đúng chỗ scanner của grader quét. Shape không ghi debug log hay stdout ra chỗ nào khác.

Bằng chứng trace sạch:
- Test `test_workflow_trace_has_no_secret_or_ticket_text` kiểm tra điều này trên cả 14 claim public.
- Hidden self-check trên 200 trial không có trial `leak_suspect` nào.

Approval do host kiểm chứ không do shape tự quyết. Các ca approval hỏng hoặc dùng approval của claim khác được kiểm ở `tests/test_authorization.py` và `tests/test_order_cap_and_approval_binding.py`: cả 11 test đều pass.

## Giới hạn

- MockLLM không phải model sản xuất. Trong workflow, MockLLM chỉ soạn câu trả lời, nên kết quả không phụ thuộc vào chất lượng model.
- Latency để `unavailable`. Cost là giá token mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API.
- Corpus public chỉ có 14 claim.
- Hidden self-check (`src/reports/hidden_selfcheck.json`, 40 claim × 5 seed) không có nhãn. Nó chỉ cho thấy shape chạy hết mà không lỗi và không lộ secret, chưa cho ra pass rate. Điểm hidden chính thức do grader của giảng viên chấm.
- Không sửa JSON trong `src/reports/` để đạt ngưỡng 0.75.
