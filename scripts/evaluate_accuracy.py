import os
import sys
import csv
import time

# Add the project root to the python path so we can import detectors
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from detectors import rule_based
from detectors import nlp_contextual
from detectors import deep_learning
from detectors.risk_scoring import calculate_risk

def evaluate():
    test_file = os.path.join(PROJECT_ROOT, "dataset", "test.csv")
    if not os.path.exists(test_file):
        print(f"Test dataset not found at {test_file}")
        return

    y_true = []
    y_pred = []

    print("Evaluating model against test.csv...")
    start_time = time.time()

    with open(test_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            text = row["text"]
            true_label = 1 if row["label"] == "sensitive" else 0
            
            # Run detection
            pattern_findings = rule_based.detect_patterns(text)
            entity_findings = nlp_contextual.extract_entities(text)
            combined = {**pattern_findings, **entity_findings}
            
            dl_result = deep_learning.predict(text)
            risk = calculate_risk(combined, dl_result)
            
            pred_label = 1 if risk["score"] > 8 else 0

            y_true.append(true_label)
            y_pred.append(pred_label)
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1} records...")

    # Calculate metrics
    true_positives = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    false_positives = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    false_negatives = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    true_negatives = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

    accuracy = (true_positives + true_negatives) / len(y_true)
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n--- Evaluation Results ---")
    print(f"Total Records Tested : {len(y_true)}")
    print(f"Accuracy             : {accuracy * 100:.2f}%")
    print(f"Precision            : {precision * 100:.2f}%")
    print(f"Recall               : {recall * 100:.2f}%")
    print(f"F1 Score             : {f1_score * 100:.2f}%")
    print("--------------------------")
    
    print(f"\nExecution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    evaluate()
