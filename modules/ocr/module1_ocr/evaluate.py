# ============================================================
# AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM
# MODULE 1: COMPREHENSIVE BENCHMARK & EVALUATION ENGINE
# ============================================================

import os
import sys
import json
import time

# Configure UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from app import process_document


def compute_levenshtein_distance(s1, s2):
    """Calculates Levenshtein edit distance between two strings."""
    s1 = str(s1 or "").upper().strip()
    s2 = str(s2 or "").upper().strip()
    
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
                
    return dp[m][n]


def compute_cer(predicted, ground_truth):
    """Computes Character Error Rate (CER) percentage."""
    gt = str(ground_truth or "").strip()
    if not gt:
        return 0.0 if not predicted else 100.0
    dist = compute_levenshtein_distance(predicted, gt)
    return min(100.0, round((dist / len(gt)) * 100.0, 2))


def run_evaluation(ground_truth_path="ground_truth.json", input_dir="input"):
    """Runs full pipeline evaluation against annotated ground truth."""
    if not os.path.exists(ground_truth_path):
        print(f"❌ Ground truth file '{ground_truth_path}' not found.")
        return

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print("\n" + "=" * 80)
    print("      AI-BASED FAKE IDENTITY & DOCUMENT SCREENING SYSTEM")
    print("           MODULE 1: BENCHMARK & ACCURACY EVALUATION")
    print("=" * 80)

    total_docs = len(ground_truth)
    total_fields = 0
    correct_fields = 0
    total_cer_sum = 0.0
    total_time_ms = 0.0
    classification_correct = 0
    manual_reviews_flagged = 0

    per_doc_results = []

    for filename, gt_fields in ground_truth.items():
        image_path = os.path.join(input_dir, filename)
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            continue

        print(f"\nEvaluating: {filename}...")
        t0 = time.perf_counter()
        try:
            res = process_document(image_path)
        except Exception as e:
            print(f"❌ Processing error on {filename}: {e}")
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        total_time_ms += elapsed_ms

        # Classification check
        gt_type = gt_fields.get("document_type")
        pred_type = res.get("document_type")
        class_match = (gt_type == pred_type)
        if class_match:
            classification_correct += 1

        if res.get("manual_review_required"):
            manual_reviews_flagged += 1

        # Flatten extracted fields for comparison
        pred_fields = {}
        for section in ["identity", "document"]:
            for k, v in res.get(section, {}).items():
                if v:
                    pred_fields[k] = v

        doc_fields_total = 0
        doc_fields_correct = 0
        doc_cer_sum = 0.0

        for field_name, gt_val in gt_fields.items():
            if field_name == "document_type":
                continue
            doc_fields_total += 1
            total_fields += 1
            pred_val = pred_fields.get(field_name)

            cer = compute_cer(pred_val, gt_val)
            doc_cer_sum += cer
            total_cer_sum += cer

            # Match criteria: exact or normalized match
            is_match = (str(pred_val).upper().strip() == str(gt_val).upper().strip())
            if is_match:
                doc_fields_correct += 1
                correct_fields += 1

        doc_acc = round((doc_fields_correct / max(1, doc_fields_total)) * 100.0, 2)
        doc_avg_cer = round(doc_cer_sum / max(1, doc_fields_total), 2)

        per_doc_results.append({
            "filename": filename,
            "document_type": pred_type,
            "classification_correct": class_match,
            "fields_evaluated": doc_fields_total,
            "fields_correct": doc_fields_correct,
            "field_accuracy_pct": doc_acc,
            "average_cer_pct": doc_avg_cer,
            "processing_time_ms": round(elapsed_ms, 2),
            "manual_review_required": res.get("manual_review_required", False)
        })

    # Summary Metrics
    overall_field_accuracy = round((correct_fields / max(1, total_fields)) * 100.0, 2)
    overall_avg_cer = round(total_cer_sum / max(1, total_fields), 2)
    overall_class_accuracy = round((classification_correct / max(1, total_docs)) * 100.0, 2)
    avg_time_ms = round(total_time_ms / max(1, total_docs), 2)
    manual_review_rate = round((manual_reviews_flagged / max(1, total_docs)) * 100.0, 2)

    print("\n" + "-" * 80)
    print("📊 BENCHMARK RESULTS TABLE")
    print("-" * 80)
    print(f"{'Document File':<22} | {'Type':<16} | {'Accuracy':<10} | {'Avg CER':<9} | {'Latency':<10} | {'Review'}")
    print("-" * 80)
    for r in per_doc_results:
        rev_tag = "⚠️ REQ" if r["manual_review_required"] else "✅ OK"
        print(f"{r['filename']:<22} | {r['document_type']:<16} | {r['field_accuracy_pct']:>8}% | {r['average_cer_pct']:>7}% | {r['processing_time_ms']:>7} ms | {rev_tag}")

    print("=" * 80)
    print(f"🎯 OVERALL METRICS SUMMARY:")
    print(f"  - Document Classification Accuracy : {overall_class_accuracy}%")
    print(f"  - Field-Level Extraction Accuracy : {overall_field_accuracy}%")
    print(f"  - Average Character Error Rate     : {overall_avg_cer}%")
    print(f"  - Average Processing Time          : {avg_time_ms} ms/doc")
    print(f"  - Human Operator Review Trigger Rate: {manual_review_rate}%")
    print("=" * 80)

    # Save to JSON
    report = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_documents_tested": total_docs,
        "classification_accuracy_pct": overall_class_accuracy,
        "field_accuracy_pct": overall_field_accuracy,
        "average_cer_pct": overall_avg_cer,
        "average_latency_ms": avg_time_ms,
        "manual_review_rate_pct": manual_review_rate,
        "per_document_results": per_doc_results
    }
    os.makedirs("output", exist_ok=True)
    with open("output/evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print("💾 Evaluation Report saved to: output/evaluation_report.json\n")


if __name__ == "__main__":
    run_evaluation()
