import sys
from pathlib import Path
import torch
import torchvision.models as tvm
from torch.utils.data import DataLoader
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset

config_path = Path(__file__).parent / "configs" / "training_config.yaml"
with open(config_path) as f:
    cfg = yaml.safe_load(f)

test_ds = KneeOADataset(cfg["dataset"]["root"], "test", cfg, is_training=False)
loader = DataLoader(test_ds, batch_size=32, shuffle=False)

print("=" * 55)
print("TEST SET ACCURACY COMPARISON (540 IMAGES)")
print("=" * 55)

checkpoints_dir = Path(__file__).parent / "checkpoints"

for arch, filename in [
    ("EfficientNet-B0", "efficientnet_b0_best.pth"),
    ("MobileNetV3-Large", "mobilenet_v3_large_best.pth"),
]:
    path = checkpoints_dir / filename
    if "Efficient" in arch:
        m = tvm.efficientnet_b0(weights=None)
        m.classifier[-1] = torch.nn.Linear(m.classifier[-1].in_features, 3)
    else:
        m = tvm.mobilenet_v3_large(weights=None)
        m.classifier[-1] = torch.nn.Linear(m.classifier[-1].in_features, 3)

    state = torch.load(path, map_location="cpu", weights_only=True)
    m.load_state_dict(state)
    m.eval()

    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in loader:
            preds = m(x).argmax(dim=1)
            correct += (preds == y).sum().item()
            total += len(y)

    acc = round(correct / total * 100, 2)
    print(f"  {arch:<20} | Test Accuracy: {correct}/{total} ({acc}%)")

print("=" * 55)
