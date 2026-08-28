# BoneVision 🦴

> **AI-Assisted Knee Osteoporosis Screening** — Research Prototype

BoneVision is a production-quality AI screening prototype that analyzes knee X-ray images to classify them as **Normal**, **Osteopenia**, or **Osteoporosis** using transfer learning with explainability (Grad-CAM).

> ⚠️ **Medical Disclaimer**: This is a research tool, NOT a substitute for clinical diagnosis. All results must be confirmed by a qualified radiologist.

---

## Project Structure

```
BoneVision/
├── frontend/          # React + Vite UI
├── backend/           # FastAPI Python backend
├── ml_pipeline/       # Training & evaluation scripts
└── data/              # Dataset (not committed to git)
```

---

## Quick Start

### 1. Frontend (Demo Mode — no backend needed)

```bash
cd frontend
npm install
npm run dev
```
Opens at http://localhost:5173 — fully functional in demo mode.

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs at http://localhost:8000/docs

### 3. ML Pipeline (requires dataset)

```bash
cd ml_pipeline
pip install -r ../backend/requirements.txt
python check_setup.py           # Verify environment
python 01_data_validation.py    # Validate dataset
python 02_train.py              # Train (CPU: ~2-3 hours)
python 04_calibrate.py          # Calibrate probabilities
python 03_evaluate.py           # Final test set evaluation
python 05_gradcam_samples.py    # Generate Grad-CAM visualisations
python 06_export_model.py       # Export model for backend
```

After step 6, restart the backend — it will automatically load the trained model.

---

## Dataset

**Knee Osteoarthritis Classification**
- Train: 3,780 images (1,260 per class)
- Val: 1,080 images (360 per class)
- Test: 540 images (180 per class)
- Classes: Normal, Osteopenia, Osteoporosis

---

## Model

- Architecture: EfficientNet-B0 and MobileNetV3-Large compared (best selected by val AUC)
- Pretrained on ImageNet, fine-tuned on dataset
- Confidence threshold: 0.60 (below → UNCERTAIN)
- Calibrated with Temperature Scaling

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/analyze | Upload X-ray, get prediction |
| GET | /api/v1/health | API health check |
| GET | /api/v1/model-info | Model metadata and metrics |

---

## Accuracy / Safety Guarantees

- Test set is NEVER touched during training or tuning
- Patient-level split is preserved (pre-split dataset)
- Uncertain results are always flagged, never forced
- All predictions include medical disclaimer
- Model performance is reported honestly from held-out test set
