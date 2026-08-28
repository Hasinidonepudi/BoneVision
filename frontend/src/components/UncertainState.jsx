import { motion } from 'framer-motion'
import { HelpCircle } from 'lucide-react'

const REASONS = [
  'Image quality may be insufficient for reliable analysis',
  'Unusual bone presentation outside the training distribution',
  'Ambiguous features between two or more classes',
  'Image may not be a standard knee X-ray view',
]

export default function UncertainState({ confidence }) {
  const pct = Math.round((confidence ?? 0) * 100)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-2xl border border-slate-600 bg-slate-800/50 p-6 text-center"
    >
      <div className="flex flex-col items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-slate-700/50 border border-slate-600 flex items-center justify-center">
          <HelpCircle className="w-8 h-8 text-slate-400" />
        </div>

        <div>
          <h3 className="text-xl font-bold text-slate-300 mb-1">
            Insufficient Confidence
          </h3>
          <p className="text-slate-400 text-sm">This image requires manual specialist review</p>
        </div>

        <div className="bg-slate-900/50 rounded-xl px-6 py-3">
          <p className="text-slate-500 text-xs mb-1">Model Confidence</p>
          <p className="text-3xl font-bold text-slate-400">{pct}%</p>
          <p className="text-slate-600 text-xs mt-1">Threshold: 60%</p>
        </div>

        <div className="w-full text-left">
          <p className="text-slate-400 text-sm font-medium mb-2">Possible reasons:</p>
          <ul className="space-y-2">
            {REASONS.map((reason, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-500">
                <span className="mt-0.5 shrink-0 w-4 h-4 rounded-full bg-slate-700 flex items-center justify-center text-xs">
                  {i + 1}
                </span>
                {reason}
              </li>
            ))}
          </ul>
        </div>

        <div className="w-full p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-sm text-center">
          Please refer this case to a qualified radiologist for clinical evaluation.
        </div>
      </div>
    </motion.div>
  )
}
