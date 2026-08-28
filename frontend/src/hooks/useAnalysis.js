// useAnalysis hook
// Manages the full analysis state machine: idle → steps → done/error
// Simulates step-by-step progress even in demo mode for realistic UX.

import { useState, useCallback } from 'react'
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

const STEP_DELAYS = {
  [ANALYSIS_STATES.UPLOADING]: 0,
  [ANALYSIS_STATES.VALIDATING]: 600,
  [ANALYSIS_STATES.PREPROCESSING]: 1200,
  [ANALYSIS_STATES.ANALYZING]: 1900,
}

export function useAnalysis() {
  const [state, setState] = useState(ANALYSIS_STATES.IDLE)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const analyze = useCallback(async (file) => {
    setResult(null)
    setError(null)

    // Kick off step progression
    setState(ANALYSIS_STATES.UPLOADING)

    const stepTimers = []

    // Schedule simulated step transitions
    Object.entries(STEP_DELAYS).forEach(([step, ms]) => {
      if (ms > 0) {
        const t = setTimeout(() => setState(step), ms)
        stepTimers.push(t)
      }
    })

    try {
      const data = await analyzeImage(file)
      stepTimers.forEach(clearTimeout)
      setState(ANALYSIS_STATES.DONE)
      setResult(data)

      // Persist to history
      saveToHistory({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        filename: file.name,
        status: data.status,
        predicted_class: data.predicted_class,
        confidence: data.confidence,
        demo_mode: data.demo_mode,
      })
    } catch (err) {
      stepTimers.forEach(clearTimeout)
      setState(ANALYSIS_STATES.ERROR)
      setError(err.message || 'Analysis failed. Please try again.')
    }
  }, [])

  const reset = useCallback(() => {
    setState(ANALYSIS_STATES.IDLE)
    setResult(null)
    setError(null)
  }, [])

  return { state, result, error, analyze, reset }
}

// ---------------------------------------------------------------------------
// LocalStorage history helpers
// ---------------------------------------------------------------------------
const HISTORY_KEY = 'bonevision_history'

export function saveToHistory(entry) {
  try {
    const existing = getHistory()
    const updated = [entry, ...existing].slice(0, 50) // Keep max 50
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
  } catch {
    // localStorage might be unavailable
  }
}

export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY)
}
