import json
import os
from collections import Counter

def cluster_failures(results_path):
    if not os.path.exists(results_path):
        print(f"❌ File {results_path} không tồn tại.")
        return

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Lọc các case có điểm < 4.0 (bao gồm cả fail)
    failures = [item for item in data if item.get('judge', {}).get('final_score', 5) < 4.0]
    
    print(f"📊 Tìm thấy {len(failures)} cases cần phân tích.")
    
    clusters = {
        "Hallucination": 0,
        "Incomplete/No Info": 0,
        "Retrieval Fail": 0,
        "Adversarial Success": 0,
        "Unknown": 0
    }
    
    for fail in failures:
        reason = str(fail.get('judge', {}).get('reasoning', '')).lower()
        answer = str(fail.get('agent_response', '')).lower()
        
        if "do not contain information" in answer or "no information" in answer:
            clusters["Incomplete/No Info"] += 1
        elif "incorrectly states" in reason or "inaccurate" in reason or "hallucinat" in reason:
            clusters["Hallucination"] += 1
        elif "retrieval" in reason or "not found in context" in reason:
            clusters["Retrieval Fail"] += 1
        elif "injection" in reason or "adversarial" in reason:
            clusters["Adversarial Success"] += 1
        else:
            clusters["Unknown"] += 1
            
    print("\n📈 Thống kê Phân nhóm Lỗi Thực tế:")
    for group, count in clusters.items():
        percentage = (count / len(failures) * 100) if len(failures) > 0 else 0
        print(f"- {group}: {count} ({percentage:.1f}%)")

    # Tìm 3 case tệ nhất (điểm thấp nhất)
    worst_cases = sorted(failures, key=lambda x: x['judge']['final_score'])[:3]
    print("\n🆘 TOP 3 CASE TỆ NHẤT ĐỂ LÀM 5 WHYS:")
    for i, case in enumerate(worst_cases, 1):
        print(f"{i}. Score: {case['judge']['final_score']} | Q: {case['test_case'][:100]}...")

if __name__ == "__main__":
    cluster_failures("reports/benchmark_results.json")
