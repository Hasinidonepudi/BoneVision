import { motion } from 'framer-motion'
import { ShieldCheck, Scan, Cpu, CheckCircle2 } from 'lucide-react'
import { ANALYSIS_STATES } from '../hooks/useAnalysis'

const STEPS = [
  { id: ANALYSIS_STATES.VALIDATING,    label: 'Validating',    icon: ShieldCheck },
  { id: ANALYSIS_STATES.PREPROCESSING, label: 'Preprocessing', icon: Scan },
  { id: ANALYSIS_STATES.ANALYZING,     label: 'Analyzing',     icon: Cpu },
  { id: ANALYSIS_STATES.DONE,          label: 'Complete',      icon: CheckCircle2 },
]

const ORDER = [
  ANALYSIS_STATES.UPLOADING,
  ANALYSIS_STATES.VALIDATING,
  ANALYSIS_STATES.PREPROCESSING,
  ANALYSIS_STATES.ANALYZING,
  ANALYSIS_STATES.DONE,
]

function stepStatus(stepId, currentState) {
  const currentIdx = ORDER.indexOf(currentState)
  const stepIdx = ORDER.indexOf(stepId)
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'active'
  return 'pending'
}

export default function AnalysisProgress({ state }) {
  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between relative">
        {/* Connecting line */}
        <div className="absolute left-0 right-0 top-5 h-0.5 bg-slate-700 z-0" />

        {STEPS.map((step, i) => {
          const status = stepStatus(step.id, state)
          const Icon = step.icon
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center gap-2 flex-1">
              <motion.div
                initial={false}
                animate={
                  status === 'active'
                    ? { scale: [1, 1.1, 1], transition: { repeat: Infinity, duration: 1.2 } }
                    : { scale: 1 }
                }
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                  status === 'done'
                    ? 'bg-green-500 border-green-500 text-white'
                    : status === 'active'
                    ? 'bg-sky-500/20 border-sky-400 text-sky-400'
                    : 'bg-slate-800 border-slate-600 text-slate-500'
                }`}
              >
                {status === 'active' ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
                  >
                    <Icon className="w-4 h-4" />
                  </motion.div>
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </motion.div>
              <span
                className={`text-xs font-medium text-center ${
                  status === 'done'
                    ? 'text-green-400'
                    : status === 'active'
                    ? 'text-sky-400'
                    : 'text-slate-500'
                }`}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
