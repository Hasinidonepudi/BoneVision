import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Upload, CheckCircle2, AlertTriangle, HelpCircle, Clock, Activity } from 'lucide-react'
import { getHistory } from '../hooks/useAnalysis'

const STATUS_ICONS = {
  NORMAL: { Icon: CheckCircle2, color: 'text-green-400' },
  ABNORMAL: { Icon: AlertTriangle, color: 'text-amber-400' },
  UNCERTAIN: { Icon: HelpCircle, color: 'text-slate-400' },
}

export default function Dashboard() {
  const history = getHistory()
  const recent = history.slice(0, 5)

  const normal = history.filter((h) => h.status === 'NORMAL').length
  const abnormal = history.filter((h) => h.status === 'ABNORMAL').length
  const uncertain = history.filter((h) => h.status === 'UNCERTAIN').length

  const stats = [
    { label: 'Total Scans', value: history.length, color: 'text-sky-400', icon: Activity },
    { label: 'Normal', value: normal, color: 'text-green-400', icon: CheckCircle2 },
    { label: 'Abnormal', value: abnormal, color: 'text-amber-400', icon: AlertTriangle },
    { label: 'Needs Review', value: uncertain, color: 'text-slate-400', icon: HelpCircle },
  ]

  return (
    <div className="min-h-screen pt-20 px-4 pb-12">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-slate-100">Dashboard</h1>
          <p className="text-slate-400 mt-1">Overview of your screening activity</p>
        </motion.div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-5"
            >
              <s.icon className={`w-5 h-5 mb-3 ${s.color}`} />
              <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-slate-400 text-sm mt-1">{s.label}</p>
            </motion.div>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Recent scans */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="md:col-span-2 bg-slate-800 border border-slate-700 rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-slate-200 font-semibold">Recent Scans</h2>
              <Link to="/history" className="text-sky-400 text-sm hover:text-sky-300 transition-colors">
                View all →
              </Link>
            </div>

            {recent.length > 0 ? (
              <div className="space-y-3">
                {recent.map((entry) => {
                  const { Icon, color } = STATUS_ICONS[entry.status] || STATUS_ICONS.UNCERTAIN
                  return (
                    <div
                      key={entry.id}
                      className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-xl"
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-slate-300 text-sm font-medium truncate">{entry.filename}</p>
                        <p className="text-slate-500 text-xs">{entry.predicted_class}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className={`text-xs font-semibold ${color}`}>
                          {Math.round(entry.confidence * 100)}%
                        </p>
                        <p className="text-slate-600 text-xs">
                          {new Date(entry.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center gap-3">
                <Clock className="w-10 h-10 text-slate-600" />
                <p className="text-slate-400">No scans yet</p>
                <Link
                  to="/analysis"
                  className="text-sky-400 text-sm hover:text-sky-300 transition-colors"
                >
                  Start your first analysis →
                </Link>
              </div>
            )}
          </motion.div>

          {/* CTA card */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-sky-900/40 to-indigo-900/40 border border-sky-500/30 rounded-2xl p-6 flex flex-col items-center justify-center text-center gap-4"
          >
            <div className="w-14 h-14 bg-sky-500/20 rounded-2xl flex items-center justify-center">
              <Upload className="w-7 h-7 text-sky-400" />
            </div>
            <div>
              <h3 className="text-slate-200 font-semibold text-lg">New Analysis</h3>
              <p className="text-slate-400 text-sm mt-1">
                Upload a knee X-ray to run a new screening
              </p>
            </div>
            <Link
              to="/analysis"
              className="w-full py-3 bg-sky-500 hover:bg-sky-400 text-white font-semibold rounded-xl transition-colors text-sm"
            >
              Start Screening
            </Link>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
