# Kịch bản thuyết trình — Lab 8 LogiX-VN (nhóm 3npc)

> **Bản nháp.** Mỗi người đọc lại phần của mình và sửa lời cho tự nhiên. Số liệu lấy từ `src/reports/` tại commit chốt `7a3eb61`; output lệnh live là output thật đã chạy thử.

**Tổng thời gian:** khoảng 8 phút trình bày, cộng hỏi đáp.
**Công cụ:** trang `demo/index.html` (mở bằng trình duyệt, không cần server) và một cửa sổ terminal trong `src/`.

## Phân vai

| Trang | Nội dung | Người nói | Thời gian |
| --- | --- | --- | --- |
| 0–3 | Tổng quan, bài toán, 4 kiến trúc, ranh giới code/model | P2 Trần Quang Hà | 2 phút 30 |
| 4–5 + terminal | Mô phỏng claim, crash và chạy live | P1 Nguyễn Minh Phương | 2 phút |
| 6 | Bảo mật trace và handoff | P3 Đoàn Trí Hùng | 30 giây |
| 7–8 | Benchmark và trace thật | P4 Ngô Minh Cương | 2 phút |
| 9 | Quyết định kiến trúc, giới hạn, mời hỏi đáp | P3 Đoàn Trí Hùng | 1 phút |

## Chuẩn bị trước giờ trình bày (P1)

1. Kéo `main` mới nhất. Trong `src/`, kích hoạt `.venv` và chạy `python -m lab8.smoke` để chắc môi trường chạy được.
2. Xóa DB cũ của buổi tập để lệnh live chạy từ đầu: `data/demo.sqlite`, `data/demo-swarm.sqlite` và `data/crash.sqlite`. Các file này đã có trong `.gitignore`.
3. Mở `demo/index.html` trên máy chiếu, bấm **F** để vào toàn màn hình. Nếu cần lời nhắc, bấm **N** để hiện ghi chú thuyết trình trên từng trang.
4. Mở sẵn terminal ở thư mục `src/`, cỡ chữ đủ lớn để cả phòng đọc được.

**Điều khiển trang:** ← → để chuyển trang, chấm số ở dưới để nhảy trang, Esc để đóng hộp chi tiết.

---

## Trang 0 · Tổng quan — P2 (30 giây)

> "Nhóm 3npc xử lý claim hoàn phí ship của LogiX-VN bằng bốn kiến trúc, từ workflow cố định tới swarm nhiều agent. Câu hỏi nhóm muốn trả lời: bài toán này có thật sự cần multi-agent không?
>
> Bốn con số bên phải là kết quả cuối: workflow đúng 70 trên 70 trial, crash 20 trên 20 kịch bản vẫn chỉ trả tiền một lần, không có refund nào khi thiếu approval hợp lệ, và không lộ secret trong 600 trial tự kiểm trên bộ hidden. Phần sau giải thích vì sao có được các số này."

**Thao tác (nếu có thời gian):** bấm ⓘ cạnh **100%** để cho thấy đây là 70 trial thật, mỗi dòng là một test case.

## Trang 1 · Bài toán — P2 (30 giây)

> "Mỗi claim có hai nguồn: ticket do khách viết và dòng order trong database. Ở claim C-002, khách viết 'trễ 5 ngày', nhưng order ghi 2 ngày. Luật là trễ từ 3 ngày mới được hoàn, nên đáp án đúng là từ chối. Hệ thống chỉ được tin order; ticket là dữ liệu, không phải lệnh."

**Thao tác:** bấm ⓘ cạnh **denied** để mở test case C-002. Chỉ vào ô đỏ duy nhất trong lưới, là swarm ở seed 55, rồi nói: "Ví dụ này sẽ quay lại ở phần trace." Bấm Esc để đóng.

## Trang 2 · Bốn kiến trúc — P2 (1 phút)

> "Đây là thang tự chủ từ A đến D. Càng sang phải, model được quyết nhiều hơn."

**Thao tác:** bấm lần lượt **workflow → single → orchestrator → swarm**. Ở mỗi shape, chỉ vào hai dòng *Ai tính tiền* và *Ai ghi refund*.

> "Ở cả ba shape nhóm viết, tiền luôn do code tính và host ghi. Khác nhau chỉ ở chỗ ai đi tìm dữ liệu: code theo thứ tự cố định, một agent ReAct, hay investigator qua handoff. Riêng swarm cho model ghi đè dữ kiện, và đó là chỗ nó sai."

## Trang 3 · Code và model — P2 (30 giây)

> "Đây là câu người chấm hay hỏi nhất. Tiền do `compute_compensation` tính, ghi sổ do `durability.issue_refund` làm, model không chạm vào cả hai. Model chỉ chọn tool đọc hoặc soạn câu trả lời."

**Thao tác:** chỉ vào hộp T14 và bấm ⓘ.

> "Đơn O-515 đã được hoàn 30.000, nay hỏng hàng nên được 150.000. Nhóm truyền đủ 150.000, host tự trừ và ghi 120.000. Nếu shape tự trừ trước thì host trừ thêm lần nữa và sai."

## Trang 4 · Mô phỏng claim — P1 (1 phút)

**Thao tác:** chọn **T02 · Ticket nói dối**, bấm **▶ Chạy**.

> "Workflow đọc order thấy trễ 2 ngày, quote ra 0, dừng ở bước 5 và không gọi host."

**Thao tác:** chọn **T13 · Đơn đã hoàn**, bấm **▶ Chạy**, rồi bấm **ⓘ Xem test case**.

> "Ở T13 quote là 35.000, lớn hơn 0, nên shape phải gọi host. Host thấy đơn đã được hoàn đủ, từ chối và ghi audit `policy_denied`. Nếu shape tự từ chối thì không có audit và bị chấm fail."

## Terminal · Chạy live — P1 (1 phút)

Chạy trong `src/`:

```bash
python -m lab8.run --shape workflow --claim-id C-002 --seed 55 --db data/demo.sqlite
```

Output cần chỉ vào: `"status": "denied"`, `"proposal_amount": 0`, `"refund_effects": []`.

```bash
python -m lab8.run --shape swarm --claim-id C-002 --seed 55 --db data/demo-swarm.sqlite
```

Output cần chỉ vào: `"status": "resolved"`, `"proposal_amount": 20000`, một dòng refund 20.000.

> "Cùng claim, cùng seed: workflow từ chối đúng, swarm trả 20.000 vì tin số ngày trong ticket."

## Trang 5 · Crash — P1 (1 phút)

Chạy trong terminal:

```bash
python -m lab8.run --shape workflow --claim-id C-012 --seed 11 --db data/crash.sqlite --crash-at after_effect_before_checkpoint
```

Output: `{"crashed": true, "at": "after_effect_before_checkpoint", "claim_id": "C-012"}`.

```bash
python -m lab8.run --shape workflow --claim-id C-012 --seed 11 --db data/crash.sqlite
```

Output: `"status": "resolved"`, đúng **một** dòng refund 35.000 với khóa `refund:C-012`, `"committed_audit_count": 1`.

**Thao tác trên trang:** bấm ô đỏ **after_effect_before_checkpoint**.

> "Đây là trường hợp nguy hiểm nhất: tiền đã ghi nhưng checkpoint chưa kịp lưu. Nếu chỉ dựa vào checkpoint, lần chạy lại sẽ trả thêm một lần. Ledger có khóa idempotency `refund:{claim_id}`, nên lần chạy lại không ghi thêm gì."

**Thao tác (tùy chọn):** bấm một ô **E** trong lưới 20 ô để mở kịch bản crash tương ứng.

## Trang 6 · Bảo mật — P3 (30 giây)

> "Trace là ranh giới bảo mật, không phải log debug. Grader quét mọi file trace, nên nhóm không ghi ticket, claim row hay order row thô. Handoff cho investigator dựng bằng allowlist trong code, `facts` để trống và chỉ có tool đọc.
>
> Một bản tóm tắt bằng LLM không phải là redaction, vì model vẫn có thể chép lại secret. Nhóm lọc bằng allowlist, nên field nào không có tên trong danh sách thì không ra khỏi ranh giới được."

## Trang 7 · Benchmark — P4 (1 phút)

**Thao tác:** bấm lần lượt **Pass rate → Pass^5 → Cost / success**.

> "Cùng 14 claim, cùng 5 seed, cùng bảng giá. Ba shape nhóm viết đều đúng 100%, swarm 98,6%. Pass^5 cho thấy chênh lệch rõ hơn: chỉ 92,9% claim của swarm đúng cả 5 lần chạy.
>
> Về chi phí, workflow 28,79 đồng mỗi lần đúng, orchestrator 56,88, gần gấp đôi. Thêm agent không làm đúng hơn, chỉ làm đắt hơn."

**Thao tác:** bấm ô **92,9%** của swarm ở seed 55 trong heatmap, rồi bấm dòng **C-002** để mở test case bị sai.

## Trang 8 · Trace thật — P4 (1 phút)

> "Đây là trace thật của cùng claim C-002 ở seed 55. Đọc cột swarm từ trên xuống: investigator đã thấy `delay_days: 2`, nhưng sau đó có event `model_override` đổi thành 5 ngày lấy từ ticket, nên quote ra 20.000. Hai cột còn lại quote từ order row nên ra 0 và từ chối. Đây là lý do tiền phải do code tính."

## Trang 9 · Quyết định — P3 (1 phút)

> "Nhóm chọn workflow: đúng bằng single và orchestrator, rẻ bằng một nửa orchestrator, ít bước và dễ kiểm toán nhất. Bài toán là chuỗi tuần tự, không có phần nào cần chạy song song.
>
> Kết luận này có giới hạn: MockLLM không phải model thật, latency không đo, và bộ public chỉ có 14 claim. Quyết định sẽ đổi nếu claim cần đọc văn bản tự do mà code không trích được, nếu có nhiều nguồn dữ liệu độc lập chạy song song được, hoặc nếu model thật cho kết quả đúng hơn với chi phí chấp nhận được.
>
> Nhóm chọn shape đơn giản nhất qua được mọi cổng. Multi-agent chỉ đáng dùng khi dữ liệu cho thấy nó đúng hơn, không phải vì nó nghe hiện đại hơn. Nhóm xin nhận câu hỏi."

---

## Chuẩn bị hỏi đáp

`RULES.md` ghi rõ người chấm có thể hỏi trực tiếp các câu dưới đây. Ai cũng nên trả lời được.

| Câu hỏi | Trả lời ngắn | Ai trả lời chính |
| --- | --- | --- |
| Vì sao chọn workflow? | Pass 1.000 bằng single và orchestrator, variance 0, cost/success 28,79 thấp nhất, ít tự chủ nhất. Xem `report/team/decision_adr.md` | P1 |
| Ranh giới code và model trong shape của nhóm? | Code đọc dữ liệu qua tool allowlist, tính tiền bằng `compute_compensation`; host ghi bằng `issue_refund`. Model chỉ soạn câu trả lời (workflow), chọn tool đọc (single) hoặc lập kế hoạch giao việc (orchestrator) | P2 |
| Vì sao truyền quote đầy đủ vào `issue_refund`? | Host tự trừ phần đơn đã được hoàn theo trần của đơn. Shape tự trừ thì bị trừ hai lần, T14 fail | P1 |
| Trace cố ý không ghi field nào? | Ticket, claim row (`parent_secret`, `raw_headers`), order row thô (SĐT, địa chỉ, tên hàng, ghi chú nội bộ) | P3 |
| Vì sao checkpoint không thay được ledger? | Crash sau khi ghi tiền mà trước checkpoint thì checkpoint báo "chưa trả". Chỉ khóa idempotency trong ledger mới chặn được lần trả thứ hai | P4 |
| Vì sao workflow và single có chi phí bằng nhau? | `decide` của single hiện là code tất định và chưa tính mỗi bước là một lần gọi model, nên đi đúng các tool như workflow. Chi phí mô phỏng chủ yếu là tiền tool (10 đồng mỗi lần), token chỉ khoảng 0,9 đồng | P2 |
| Vì sao swarm chỉ sai ở seed 55? | Khối `REFERENCE_WEAKNESS` chỉ tin số ngày trong ticket khi seed chia hết cho 5, và chỉ C-002 có ticket ghi số ngày khác với DB | P4 |
| Công cụ AI đã dùng và cách tự kiểm? | Mỗi người ghi trong báo cáo cá nhân; mọi số liệu đều là output lệnh đã chạy lại | Từng người |

## Phương án dự phòng

- **Terminal lỗi hoặc thiếu thời gian:** bỏ phần chạy live; trang 4 và 5 đã có mô phỏng bấm được, nút ⓘ mở test case thật.
- **Máy chiếu thấp (1366×768):** vài trang dư vài chục pixel; cuộn nhẹ bên trong trang.
- **Lệnh live báo DB đã tồn tại:** `lab8.run` chạy lại trên cùng DB là kịch bản resume. Muốn chạy từ đầu thì xóa file `.sqlite` hoặc đổi tên `--db`.
