// BoneVision API Service
// Handles communication with FastAPI backend.
// Falls back to demo mode when backend is unreachable or VITE_DEMO_MODE=true.

import axios from 'axios'

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// ---------------------------------------------------------------------------
// Demo prediction data — realistic mock outcomes
// ---------------------------------------------------------------------------
const DEMO_OUTCOMES = [
  {
    status: 'NORMAL',
    predicted_class: 'Normal',
    confidence: 0.88,
    predictions: [
      { class: 'Normal', probability: 0.88 },
      { class: 'Osteopenia', probability: 0.08 },
      { class: 'Osteoporosis', probability: 0.04 },
    ],
  },
  {
    status: 'ABNORMAL',
    predicted_class: 'Osteopenia',
    confidence: 0.83,
    predictions: [
      { class: 'Normal', probability: 0.11 },
      { class: 'Osteopenia', probability: 0.83 },
      { class: 'Osteoporosis', probability: 0.06 },
    ],
  },
  {
    status: 'ABNORMAL',
    predicted_class: 'Osteoporosis',
    confidence: 0.79,
    predictions: [
      { class: 'Normal', probability: 0.07 },
      { class: 'Osteopenia', probability: 0.14 },
      { class: 'Osteoporosis', probability: 0.79 },
    ],
  },
  {
    status: 'UNCERTAIN',
    predicted_class: 'Osteopenia',
    confidence: 0.42,
    predictions: [
      { class: 'Normal', probability: 0.34 },
      { class: 'Osteopenia', probability: 0.42 },
      { class: 'Osteoporosis', probability: 0.24 },
    ],
  },
]

/** Simple hash from filename for deterministic demo result */
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff
  }
  return Math.abs(hash)
}

function getDemoResult(file) {
  const weights = [0.30, 0.30, 0.30, 0.10]
  const seed = hashString(file.name + file.size)
  const rand = (seed % 100) / 100

  let cumulative = 0
  let idx = 0
  for (let i = 0; i < weights.length; i++) {
    cumulative += weights[i]
    if (rand < cumulative) { idx = i; break }
  }

  const base = DEMO_OUTCOMES[idx]
  return {
    ...base,
    requires_review: base.status === 'UNCERTAIN' || base.confidence < 0.60,
    gradcam_heatmap: null,
    disclaimer:
      'This is an AI-assisted screening tool. Results must be confirmed by a qualified radiologist or healthcare professional.',
    model_version: 'bonevision-demo-v1.0',
    inference_time_ms: 120 + Math.floor(seed % 80),
    demo_mode: true,
    warnings: ['Demo mode: predictions are illustrative only and not from a trained model.'],
  }
}

// ---------------------------------------------------------------------------
// Main API function
// ---------------------------------------------------------------------------

/**
 * Analyze an X-ray image.
 * Tries the real backend first; falls back to demo mode on failure.
 * @param {File} file - Image file to analyze
 * @returns {Promise<Object>} Analysis response matching AnalysisResponse schema
 */
export async function analyzeImage(file) {
  if (DEMO_MODE) {
    console.log('[BoneVision] Demo mode active — skipping backend call')
    await delay(2500)
    return getDemoResult(file)
  }

  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    console.log('[BoneVision] Backend response:', response.data)
    return response.data
  } catch (err) {
    console.warn('[BoneVision] Backend unavailable, using demo mode:', err.message)
    await delay(2500)
    return getDemoResult(file)
  }
}

/**
 * Get model metadata and metrics.
 * @returns {Promise<Object>} Model info response
 */
export async function getModelInfo() {
  if (DEMO_MODE) {
    return {
      classes: ['Normal', 'Osteopenia', 'Osteoporosis'],
      model_version: 'bonevision-demo-v1.0',
      confidence_threshold: 0.60,
      metrics: null,
      demo_mode: true,
      architecture: 'efficientnet_b0',
    }
  }
  try {
    const res = await api.get('/model-info')
    return res.data
  } catch {
    return null
  }
}

/**
 * Health check.
 * @returns {Promise<Object|null>}
 */
export async function checkHealth() {
  try {
    const res = await api.get('/health')
    return res.data
  } catch {
    return null
  }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
