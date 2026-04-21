import json
import os

def validate():
    corpus_path = "data/source_corpus.json"
    golden_path = "data/golden_set.jsonl"
    
    if not os.path.exists(corpus_path) or not os.path.exists(golden_path):
        print("❌ Error: Missing required files.")
        return

    # Load corpus IDs
    with open(corpus_path, "r") as f:
        corpus = json.load(f)
        valid_ids = {doc["doc_id"] for doc in corpus}

    # Validate Golden Set
    print(f"🧐 Validating {golden_path}...")
    errors = 0
    counters = {"total": 0, "adversarial": 0}
    
    with open(golden_path, "r") as f:
        for i, line in enumerate(f):
            try:
                case = json.loads(line)
                counters["total"] += 1
                
                # Check IDs
                for doc_id in case.get("expected_retrieval_ids", []):
                    if doc_id not in valid_ids:
                        print(f"  Branch {i}: Invalid doc_id {doc_id}")
                        errors += 1
                
                # Check metadata
                if case.get("metadata", {}).get("difficulty") == "adversarial":
                    counters["adversarial"] += 1
                    
            except Exception as e:
                print(f"  Line {i}: JSON Error - {e}")
                errors += 1

    print("\n--- Validation Result ---")
    print(f"✅ Total cases: {counters['total']}")
    print(f"🛡 Adversarial cases: {counters['adversarial']}")
    if errors == 0:
        print("🚀 STATUS: 100% VALID. Dataset is ready for handover!")
    else:
        print(f"❌ STATUS: FAILED. Found {errors} errors.")

if __name__ == "__main__":
    validate()
