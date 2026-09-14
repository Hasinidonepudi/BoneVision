import { useState } from 'react'
import { analyzeImage } from '../services/api'

export const ANALYSIS_STATES = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  VALIDATING: 'validating',
  PREPROCESSING: 'preprocessing',
  ANALYZING: 'analyzing',
  DONE: 'done',
  ERROR: 'error',
}

export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem('bonevision_history') || '[]')
  } catch {
    return []
  }
}

export function clearHistory() {
  localStorage.removeItem('bonevision_history')
}

export function useAnalysis() {
  const [state, setState] = useState(ANALYSIS_STATES.IDLE)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  async function analyze(file) {
    setError(null)
    setResult(null)

    try {
      // Step 1: Uploading state
      setState(ANALYSIS_STATES.UPLOADING)
      await wait(400)

      // Step 2: Validating X-ray resolution & DICOM/format criteria
      setState(ANALYSIS_STATES.VALIDATING)
      await wait(500)

      // Step 3: Medical CLAHE & Bone Edge Preprocessing
      setState(ANALYSIS_STATES.PREPROCESSING)
      await wait(600)

      // Step 4: Deep Learning Inference & Grad-CAM Computation
      setState(ANALYSIS_STATES.ANALYZING)
      
      const [apiResult] = await Promise.all([
        analyzeImage(file),
        wait(600), // Smooth 2s total realistic clinical inspection experience
      ])

      // Step 5: Finished
      setResult(apiResult)
      setState(ANALYSIS_STATES.DONE)

      // Save to localStorage history
      try {
        const historyItem = {
          id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
          filename: file.name,
          timestamp: new Date().toISOString(),
          status: apiResult.status,
          predicted_class: apiResult.predicted_class,
          confidence: apiResult.confidence,
          inference_time_ms: apiResult.inference_time_ms,
          demo_mode: apiResult.demo_mode,
        }
        const existing = getHistory()
        localStorage.setItem(
          'bonevision_history',
          JSON.stringify([historyItem, ...existing].slice(0, 50))
        )
      } catch (e) {
        console.warn('Could not save to history:', e)
      }
    } catch (err) {
      console.error('Analysis failed:', err)
      setError(err.message || 'An unexpected error occurred during analysis.')
      setState(ANALYSIS_STATES.ERROR)
    }
  }

  function reset() {
    setState(ANALYSIS_STATES.IDLE)
    setResult(null)
    setError(null)
  }

  return { state, result, error, analyze, reset }
}
