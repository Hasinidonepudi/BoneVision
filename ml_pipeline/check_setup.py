"""
BoneVision Setup Checker
Verifies your environment is ready for training.

Usage: python check_setup.py
"""
import sys
import importlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

print("=" * 55)
print("BoneVision Setup Check")
print("=" * 55)

# 1. Python version
major, minor = sys.version_info[:2]
ok = major == 3 and minor >= 9
print(f"{'✅' if ok else '❌'} Python {major}.{minor} {'(OK)' if ok else '(Need 3.9+)'}")

# 2. Required packages
packages = {
    "torch": "PyTorch",
    "torchvision": "TorchVision",
    "PIL": "Pillow",
    "cv2": "OpenCV",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "tqdm": "tqdm",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "scipy": "SciPy",
}

all_ok = True
for pkg, name in packages.items():
    try:
        mod = importlib.import_module(pkg)
        ver = getattr(mod, "__version__", "?")
        print(f"✅ {name:<15} v{ver}")
    except ImportError:
        print(f"❌ {name:<15} NOT INSTALLED — run: pip install -r backend/requirements.txt")
        all_ok = False

# 3. GPU check
try:
    import torch
    if torch.cuda.is_available():
        print(f"\n🎮 GPU: {torch.cuda.get_device_name(0)} (CUDA {torch.version.cuda})")
    else:
        print(f"\n💻 GPU: Not available — CPU-only training mode")
        print(f"   ⏱  Estimated training time: ~60–120 min per architecture")
except Exception:
    pass

# 4. Dataset check
from pathlib import Path
import yaml

config_path = Path(__file__).parent / "configs" / "training_config.yaml"
if config_path.exists():
    with open(config_path) as f:
        config = yaml.safe_load(f)
    root = Path(config["dataset"]["root"])
    print(f"\n📁 Dataset root: {root}")
    if root.exists():
        total = 0
        for split in ["train", "val", "test"]:
            for cls in config["dataset"]["classes"]:
                d = root / split / cls
                n = len(list(d.glob("*.*"))) if d.exists() else 0
                total += n
        print(f"✅ Dataset found — {total} total images")
    else:
        print(f"❌ Dataset NOT found at: {root}")
        all_ok = False
else:
    print(f"❌ training_config.yaml not found")
    all_ok = False

print("\n" + "=" * 55)
if all_ok:
    print("✅ Setup OK — Ready to train!")
    print("   Next: python ml_pipeline/01_data_validation.py")
    print("   Then: python ml_pipeline/02_train.py")
else:
    print("⚠️  Fix the issues above before training.")
print("=" * 55)
