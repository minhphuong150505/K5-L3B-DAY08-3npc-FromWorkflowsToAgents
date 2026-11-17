# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 · Scaling |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Kim et al. (Google Research, Google DeepMind, MIT), *Towards a Science of Scaling Agent Systems*, arXiv:2512.08296, 12/2025 (v3 04/2026), https://arxiv.org/abs/2512.08296 ; blog Google Research 28/01/2026. Loại bằng chứng: benchmark có kiểm soát (controlled evaluation) |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lợi ích của multi-agent phụ thuộc cấu trúc task: so với single-agent, hiệu năng đổi từ +80,8% trên task phân rã được (financial reasoning) tới −70,0% trên task tuần tự (sequential planning); overhead điều phối làm lợi ích giảm hoặc âm khi task không song song được |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Model LLM thật thuộc ba họ model; benchmark agentic công khai (tài chính, lập kế hoạch, ...); 1 kiến trúc single-agent và 4 kiến trúc multi-agent với cùng tool và ngân sách token. Không đo trên task có ledger ghi tiền, không có MockLLM cố định theo seed, không có cổng duyệt do host giữ |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Claims flow LogiX là chuỗi tuần tự (claim → order → quote → refund), bước sau phụ thuộc bước trước. Thêm tầng orchestrator + investigator (workflow → orchestrator) sẽ không tăng pass rate (giữ nguyên, chênh ≤ 0,01) nhưng làm cost/success tăng khoảng 1,5–2× do thêm lời gọi model (plan) và tool đọc lặp lại |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, bộ tool `lab8.tools`, seed 11/22/33/44/55, corpus `data/public_claims.jsonl` (14 claim), `config/pricing.yaml`, `as_of` 2026-11-15, evaluator `lab8.metrics`, SQLite mới cho mỗi trial, cùng hàm quote `compute_compensation` và cùng cửa ghi `durability.issue_refund`. Biến duy nhất thay đổi: topology — có hay không tầng orchestrator giao việc cho investigator chỉ đọc qua handoff (shape `workflow` so với `orchestrator`). Swarm chạy kèm làm mốc tham chiếu |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: overhead điều phối — orchestrator trả cùng kết quả nhưng tốn nhiều lời gọi hơn. Đo bằng cost/success, mean model calls, mean tool calls, mean steps; đồng thời kiểm pass rate, pass^5, seed variance không giảm và secret leak = 0 khi dữ liệu đi qua ranh giới handoff |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r1.json` (chạy trong `src/`)
- Run id / file report: `src/reports/ablation_r1.json`, 210 trial (14 claim × 5 seed × 3 shape). Run id dạng `R-<shape>-<claim>-s<seed>`, ví dụ `R-orchestrator-C-014-s55`, `R-workflow-C-014-s55`, `R-swarm-C-002-s55` (trial swarm fail)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng.**

  | Shape | Pass rate | Pass^5 | Seed variance (min–max) | Cost/success (VND mô phỏng) | Model calls TB | Tool calls TB | Steps TB |
  | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
  | workflow | 1.000 | 1.000 | 0 (1.000–1.000) | 28.79 | 1.00 | 2.79 | 4.43 |
  | orchestrator | 1.000 | 1.000 | 0 (1.000–1.000) | 56.88 | 1.86 | 5.57 | 5.36 |
  | swarm | 0.986 | 0.929 | 0.000816 (0.929–1.000) | 49.57 | 3.00 | 4.66 | 2.80 |

  Thêm tầng orchestrator + investigator không đổi pass rate (1.000 = 1.000) nhưng cost/success tăng 1,98× (56.88 so với 28.79), nằm ở cận trên khoảng dự đoán 1,5–2×. Nguyên nhân: thêm lời gọi model `plan` (1.86 so với 1.00 lời gọi mỗi trial) và investigator đọc lại claim, order, lịch sử hoàn tiền, policy (5.57 so với 2.79 tool call). Task tuần tự nên không có bước nào chạy song song để bù lại overhead. Phù hợp với hướng của CLAIM, nhưng mức −70% trong paper không tái hiện được ở đây vì investigator của nhóm là code tất định, không phải LLM tự quyết.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Pass rate của orchestrator bằng workflow một phần vì mọi quyết định (quote, approval, ghi ledger) do code giữ; MockLLM không làm sai nên hiện tượng khuếch đại lỗi giữa các agent mà paper mô tả không thể xuất hiện. Cost là giá token mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API. Corpus public chỉ 14 claim; kết luận chưa kiểm trên bộ hidden 40 claim. Kết luận sẽ đảo nếu task có các bước đọc độc lập chạy song song được (ví dụ nhiều nguồn chứng cứ cho một claim) và latency được đo thật, hoặc nếu investigator là LLM có thể bắt được lỗi mà code không bắt.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
