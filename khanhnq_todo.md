# 📋 TO-DO LIST CÁ NHÂN - Nguyễn Quốc Khánh

**Vai trò:** Data Engineer / SDG Lead
**Thời gian:** 4 Giờ
**Mục tiêu:** Hoàn thành nhiệm vụ **Dataset & SDG** (10 điểm nhóm) + Điểm cá nhân (Engineering, Technical, Problem Solving).

> ⚠️ [CRITICAL PATH] **LƯU Ý ĐẶC BIỆT:** Nhiệm vụ của bạn là chốt chặn quan trọng nhất (CRITICAL PATH) trong Giai đoạn 1. Các thành viên khác như Khải (Agent), Tấn (Performance), Nhật (LLM Judge) đều phải chờ file `data/golden_set.jsonl` của bạn để có thể test! Hãy hoàn thành nó nhanh nhất có thể.

---

## 🎯 Nhiệm vụ cốt lõi
Tạo **golden dataset $\ge$ 50 test cases** có trường `expected_retrieval_ids` (bắt buộc dùng để tính Hit Rate), bao gồm 40 regular cases và 10 Red Teaming cases.

**File phụ trách chính:**
- `data/synthetic_gen.py`
- `data/golden_set.jsonl`
- `analysis/reflections/reflection_NguyenQuocKhanh.md`

---

## ✅ Các bước thực hiện chi tiết

### 1. Thiết kế Schema & Chuẩn bị dữ liệu (15 phút - Xong trước T+0:30)
- [x] Chốt và định nghĩa schema JSONL đầy đủ cho toàn đội. Cấu trúc chuẩn:
  ```json
  {
    "question": "...",
    "expected_answer": "...",
    "context": "...",
    "expected_retrieval_ids": ["doc_001", "doc_002"],
    "metadata": {
      "difficulty": "easy|medium|hard|adversarial",
      "type": "fact-check|reasoning|adversarial|edge-case",
      "category": "..."
    }
  }
  ```
- [x] Chuẩn bị $\ge$ 10 đoạn văn bản gốc (source corpus) thuộc chủ đề AI/Tech/Policy.
- [x] Đặt tên ID cho các đoạn văn bản theo format chuẩn: `doc_001`, `doc_002`, ...
- [x] 🚨 **GIAO TIẾP:** Thông báo ngay format `doc_id` và nguồn doc này cho **Khải** để Khải khởi tạo ChromaDB trên cùng một tập ID. Thông báo Schema cho **Tấn** để chuẩn bị Evaluator.

### 2. Triển khai Synthetic Data Generation bằng LLM (45 phút - Xong trước T+1:30)
*File: `data/synthetic_gen.py`*
- [ ] Code hàm `generate_qa_from_text()` có gọi **OpenAI API thật** (hoặc model cấu hình).
- [ ] Tinh chỉnh prompt để ép LLM trả về đúng JSON Format có trường `expected_retrieval_ids`.
- [ ] Tạo **40 Regular Cases**: Có độ khó phân bổ Easy, Medium, Hard.
- [ ] Tạo **10 Red Teaming Cases** (tham khảo `data/HARD_CASES_GUIDE.md`):
  - 3 Adversarial Prompts (Prompt Injection, Goal Hijacking).
  - 3 Edge Cases (Out of Context, Ambiguous, Conflicting Info).
  - 2 Multi-turn (Context carry-over - Khó/Đánh lừa ngắt ngữ cảnh).
  - 2 Technical (Đánh lừa để stress test).
- [ ] Khảo sát script, đảm bảo lệnh khi chạy tạo ra file `data/golden_set.jsonl` chuẩn, chứa $\ge$ 50 dòng.

### 3. Kiểm tra & Bàn giao (15 phút - Khi xong Phần 2)
- [ ] Thêm hàm `validate_golden_set()` kiểm tra tính hợp lệ của format từng dòng JSON sinh ra có đúng schema không (đặc biệt `expected_retrieval_ids`).
- [ ] Chạy thử nghiệm: `python data/synthetic_gen.py` kiểm tra xem list đạt $\ge$ 50 dòng không.
- [ ] 🚨 **GIAO TIẾP:** Thông báo cho **Nhật**, **Tấn**, **Khải** là file `golden_set.jsonl` đã hoàn thiện và sẵn sàng để lấy nghiệm thu.

### 4. Viết Reflection Cá nhân (Xong trước T+3:30)
*File: `analysis/reflections/reflection_NguyenQuocKhanh.md`*
- [ ] Nêu khái niệm và tại sao cần `expected_retrieval_ids` (hỗ trợ tính Hit Rate / MRR).
- [ ] Phân tích Red Teaming là gì, và tại sao nó lại quan trọng trong kiểm thử LLM.
- [ ] Bàn luận về vấn đề Circular evaluation (dùng chính LLM để tạo dataset và sau đó đánh giá lại LLM).
- [ ] Các bí quyết/ cách để đảm bảo chất lượng của bộ Ground Truth khi sử dụng phương pháp Synthetic Data Generation (SDG).

### 5. Git & Bàn giao
- [ ] Commit độc lập bằng lệnh sau:
  ```bash
  git commit -m "feat(data): generate 50 golden cases with 10 red teaming scenarios"
  ```
- ⚠️ **LƯU Ý:** Tuyệt đối không commit vào chung file của đồng đội để phân định `git log` nộp cho giám khảo.

---

## ⏱ Timeline Cụ thể cho Khánh
* T+0:00: Bắt đầu thiết kế schema, đồng bộ ID với Khải.
* T+0:30: Triển khai Generate QA pairs (Dùng LLM Call). Tạo 40 Regular cases.
* T+1:00: Tạo 10 Red Teaming cases.
* T+1:30: ✅ Chạy validate, đẩy commit file lên branch và thông báo cho Team.
* T+2:00: Suy nghĩ và bắt đầu viết Reflection.
* T+3:30: Hoàn thành Reflection hoàn toàn.
