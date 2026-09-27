import json
import os
import sys
import joblib


def evaluate():
    model_path = "yt-sentiment-mlops/models/sentiment_model.pkl"
    benchmark_path = "yt-sentiment-mlops/ml/benchmark.json"

    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        sys.exit(1)

    print(f"Loading model from {model_path}...")
    model = joblib.load(model_path)

    if not os.path.exists(benchmark_path):
        print(f"Error: Benchmark file not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        try:
            benchmark_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding {benchmark_path}: {e}")
            sys.exit(1)

    correct = 0
    total = len(benchmark_data)

    print("\n--- Benchmark Test Predictions ---")
    for item in benchmark_data:
        if not isinstance(item, dict):
            print(f"Skipping invalid benchmark item (must be JSON object): {item}")
            continue
        text = item.get("comment") or item.get("comments") or item.get("text", "")
        expected = item.get("sentiment") or item.get("sentiments") or item.get("expected", "")
        prediction = model.predict([text])[0]

        is_correct = (str(prediction).strip().lower() == str(expected).strip().lower())
        if is_correct:
            correct += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"[{status}] Comment: \"{text}\" | Expected: {expected} | Predicted: {prediction}")

    # 4. Compute Accuracy Metric
    accuracy = correct / total if total > 0 else 0.0
    print("\n-----------------------------------")
    print(f"Benchmark Accuracy: {accuracy * 100:.2f}% ({correct}/{total})")

    MIN_ACCURACY_THRESHOLD = 0.66

    if accuracy < MIN_ACCURACY_THRESHOLD:
        print(f"\nACCURACY GATE FAILED! Model accuracy ({accuracy * 100:.2f}%) is below required threshold ({MIN_ACCURACY_THRESHOLD * 100:.2f}%).")
        sys.exit(1)

    print("\nACCURACY GATE PASSED! Model is ready for Docker packaging and deployment.")


if __name__ == "__main__":
    evaluate()