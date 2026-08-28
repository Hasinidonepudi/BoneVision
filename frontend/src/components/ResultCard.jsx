import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, AlertCircle, Clock, FlaskConical } from 'lucide-react'

const STATUS_CONFIG = {
  NORMAL: {
    label: 'Normal',
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    barColor: 'bg-green-500',
    Icon: CheckCircle2,
  },
  ABNORMAL: {
    label: 'Abnormal Detected',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    barColor: 'bg-amber-500',
    Icon: AlertTriangle,
  },
  UNCERTAIN: {
    label: 'Uncertain',
    color: 'text-slate-400',
    bg: 'bg-slate-700/30',
    border: 'border-slate-600',
    barColor: 'bg-slate-500',
    Icon: AlertCircle,
  },
}

export default function ResultCard({ result }) {
  if (!result) return null

  const cfg = STATUS_CONFIG[result.status] || STATUS_CONFIG.UNCERTAIN
  const { Icon } = cfg
  const pct = Math.round(result.confidence * 100)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border p-6 ${cfg.bg} ${cfg.border}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${cfg.bg} border ${cfg.border}`}>
            <Icon className={`w-6 h-6 ${cfg.color}`} />
          </div>
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-0.5">
              Screening Result
            </p>
            <h3 className={`text-2xl font-bold ${cfg.color}`}>{cfg.label}</h3>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {result.demo_mode && (
            <span className="flex items-center gap-1 px-2 py-1 bg-indigo-500/20 text-indigo-400 text-xs font-medium rounded-full border border-indigo-500/30">
              <FlaskConical className="w-3 h-3" />
              Demo
            </span>
          )}
          {result.requires_review && (
            <span className="px-2 py-1 bg-orange-500/20 text-orange-400 text-xs font-medium rounded-full border border-orange-500/30">
              Manual Review Required
            </span>
          )}
        </div>
      </div>

      {/* Predicted class */}
      <div className="mb-4 p-4 bg-slate-900/50 rounded-xl">
        <p className="text-slate-400 text-xs mb-1">Predicted Classification</p>
        <p className="text-slate-100 text-xl font-semibold">{result.predicted_class}</p>
      </div>

      {/* Confidence bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-400">Model Confidence</span>
          <span className={`font-bold ${cfg.color}`}>{pct}%</span>
        </div>
        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className={`h-full rounded-full ${cfg.barColor}`}
          />
        </div>
        {result.confidence < 0.6 && (
          <p className="text-slate-500 text-xs mt-1">
            ⚠️ Confidence below threshold — result may be unreliable
          </p>
        )}
      </div>

      {/* Meta */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {result.inference_time_ms} ms
        </div>
        <span className="font-mono">{result.model_version}</span>
      </div>

      {/* Disclaimer */}
      <p className="mt-4 text-xs text-slate-500 italic border-t border-slate-700/50 pt-3">
        {result.disclaimer}
      </p>
    </motion.div>
  )
}
