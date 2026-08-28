import httpx
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

base = r"C:\Users\heman\Downloads\archive_extracted\Knee Osteoarthritis Classification\test"

total = 0
correct = 0

for true_class in ["Normal", "Osteopenia", "Osteoporosis"]:
    files = glob.glob(os.path.join(base, true_class, "*.jpeg")) + glob.glob(os.path.join(base, true_class, "*.JPEG"))
    print(f"\n=== TESTING {true_class.upper()} TEST SAMPLES ===")
    for f in files[:5]:
        with open(f, "rb") as fp:
            res = httpx.post("http://127.0.0.1:8000/api/v1/analyze", files={"file": (os.path.basename(f), fp, "image/jpeg")}, timeout=10.0)
            data = res.json()
            pred = data.get("predicted_class")
            conf = round(data.get("confidence", 0) * 100, 1)
            total += 1
            if pred == true_class:
                correct += 1
                icon = "✅"
            else:
                icon = "❌"
            print(f"  {icon} {os.path.basename(f):<18} -> Predicted: {pred:<14} | Confidence: {conf}%")

print(f"\nSample Accuracy: {correct}/{total} ({round(correct/total*100, 1)}%)")
