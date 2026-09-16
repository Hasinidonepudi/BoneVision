import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, AlertCircle, FileDown } from 'lucide-react'

import UploadZone from '../components/UploadZone'
import ImagePreview from '../components/ImagePreview'
import AnalysisProgress from '../components/AnalysisProgress'
import ResultCard from '../components/ResultCard'
import ConfidenceChart from '../components/ConfidenceChart'
import GradCamOverlay from '../components/GradCamOverlay'
import UncertainState from '../components/UncertainState'
import PatientModal from '../components/PatientModal'
import PatientForm from '../components/PatientForm'
import ClinicalBMDCard from '../components/ClinicalBMDCard'
import ModelSwitcher from '../components/ModelSwitcher'
import { generatePDFReport } from '../utils/pdfExport'
import { useAnalysis, ANALYSIS_STATES } from '../hooks/useAnalysis'

const RUNNING_STATES = [
  ANALYSIS_STATES.UPLOADING,
  ANALYSIS_STATES.VALIDATING,
  ANALYSIS_STATES.PREPROCESSING,
  ANALYSIS_STATES.ANALYZING,
]

export default function Analysis() {
  const { state, result, error, analyze, reset } = useAnalysis()
  const [file, setFile] = useState(null)
  const [selectedModel, setSelectedModel] = useState('efficientnet_b0')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [patientInfo, setPatientInfo] = useState({
    id: '',
    name: 'Suresh Kumar',
    age: '54',
    gender: 'Male',
    kneeSide: 'Right Knee (AP View)',
    physician: 'Dr. Arjun Reddy — Orthopedic Specialist',
    notes: 'Knee joint stiffness, weight-bearing pain'
  })

  const isRunning = RUNNING_STATES.includes(state)
  const isDone = state === ANALYSIS_STATES.DONE
  const isError = state === ANALYSIS_STATES.ERROR
  const isIdle = state === ANALYSIS_STATES.IDLE

  function handleFileSelect(f) {
    setFile(f)
    analyze(f, selectedModel)
  }

  function handleReset() {
    reset()
    setFile(null)
  }

  function handleExportPDF(overrideInfo) {
    if (!result) return
    generatePDFReport({
      result,
      patientInfo: overrideInfo || patientInfo,
      file,
      heatmapBase64: result.gradcam_heatmap,
    })
  }

  return (
    <div className="min-h-screen pt-20 px-4 pb-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold text-slate-100">X-Ray Analysis</h1>
            <p className="text-slate-400 mt-1">Upload a knee X-ray to run AI screening</p>
          </div>
          {!isIdle && (
            <div className="flex items-center gap-3">
              {isDone && (
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-sm font-semibold transition-colors shadow-lg shadow-sky-500/20"
                >
                  <FileDown className="w-4 h-4" />
                  Download PDF Report
                </button>
              )}
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl text-sm font-medium transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                New Analysis
              </button>
            </div>
          )}
        </motion.div>

        <AnimatePresence mode="wait">
          {/* IDLE — show Patient Form and upload dropzone */}
          {(isIdle || isRunning) && (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <ModelSwitcher
                selectedModel={selectedModel}
                onSelectModel={setSelectedModel}
                disabled={isRunning}
              />
              <PatientForm patientInfo={patientInfo} setPatientInfo={setPatientInfo} />
              <UploadZone onFileSelect={handleFileSelect} disabled={isRunning} />
              
              {isIdle && (
                <p className="text-slate-500 text-xs text-center mt-4">
                  Accepts JPEG and PNG knee X-ray images up to 10 MB.
                  No image data is stored on our servers.
                </p>
              )}
            </motion.div>
          )}

          {/* RUNNING — show preview + progress */}
          {isRunning && (
            <motion.div
              key="running"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <ImagePreview file={file} />
              <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                <p className="text-slate-300 font-medium text-center mb-2">Analysing your X-ray…</p>
                <AnalysisProgress state={state} />
              </div>
              <UploadZone onFileSelect={() => {}} disabled={true} />
            </motion.div>
          )}

          {/* DONE — show results */}
          {isDone && result && (
            <motion.div
              key="done"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-5"
            >
              <div className="grid md:grid-cols-2 gap-5">
                <ImagePreview file={file} />
                <ResultCard result={result} />
              </div>

              {/* Feature 3: Clinical BMD Assessment & Continuous WHO T-Score */}
              <ClinicalBMDCard
                predictedClass={result.predicted_class}
                confidence={result.confidence}
                predictions={result.predictions}
              />

              {result.status === 'UNCERTAIN' && (
                <UncertainState confidence={result.confidence} />
              )}

              <ConfidenceChart predictions={result.predictions} />

              {/* Feature 1: Interactive Heatmap Opacity & Zoom Slider */}
              <GradCamOverlay
                file={file}
                heatmapBase64={result.gradcam_heatmap}
              />

              {/* Warnings */}
              {result.warnings?.length > 0 && (
                <div className="flex items-start gap-2 p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-300 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{result.warnings[0]}</span>
                </div>
              )}
            </motion.div>
          )}

          {/* ERROR */}
          {isError && (
            <motion.div
              key="error"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-16"
            >
              <div className="w-14 h-14 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-7 h-7 text-red-400" />
              </div>
              <h3 className="text-slate-200 font-semibold text-lg mb-2">Analysis Failed</h3>
              <p className="text-slate-400 text-sm mb-6 max-w-sm mx-auto">{error}</p>
              <button
                onClick={handleReset}
                className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-xl font-medium transition-colors"
              >
                Try Again
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <PatientModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onExport={handleExportPDF}
        />
      </div>
    </div>
  )
}
