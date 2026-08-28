import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, HelpCircle, Trash2, Clock, Upload } from 'lucide-react'
import { getHistory, clearHistory } from '../hooks/useAnalysis'

const STATUS_CONFIG = {
  NORMAL:   { label: 'Normal',   Icon: CheckCircle2, color: 'text-green-400',  bg: 'bg-green-500/10' },
  ABNORMAL: { label: 'Abnormal', Icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  UNCERTAIN:{ label: 'Uncertain', Icon: HelpCircle,  color: 'text-slate-400',  bg: 'bg-slate-700/30' },
}

export default function History() {
  const [history, setHistory] = useState(getHistory)
  const [confirmClear, setConfirmClear] = useState(false)

  function handleClear() {
    clearHistory()
    setHistory([])
    setConfirmClear(false)
  }

  return (
    <div className="min-h-screen pt-20 px-4 pb-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-3xl font-bold text-slate-100">Scan History</h1>
            <p className="text-slate-400 mt-1">{history.length} total scans stored locally</p>
          </div>
          {history.length > 0 && (
            <div>
              {confirmClear ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">Are you sure?</span>
                  <button
                    onClick={handleClear}
                    className="px-3 py-1.5 bg-red-500 hover:bg-red-400 text-white text-sm rounded-lg transition-colors"
                  >
                    Yes, clear
                  </button>
                  <button
                    onClick={() => setConfirmClear(false)}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmClear(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl text-sm font-medium transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear History
                </button>
              )}
            </div>
          )}
        </motion.div>

        {/* Table */}
        {history.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                    <th className="text-left px-6 py-4 font-medium">Date & Time</th>
                    <th className="text-left px-6 py-4 font-medium">Filename</th>
                    <th className="text-left px-6 py-4 font-medium">Status</th>
                    <th className="text-left px-6 py-4 font-medium">Classification</th>
                    <th className="text-right px-6 py-4 font-medium">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((entry, i) => {
                    const cfg = STATUS_CONFIG[entry.status] || STATUS_CONFIG.UNCERTAIN
                    const { Icon } = cfg
                    return (
                      <tr
                        key={entry.id}
                        className="border-b border-slate-700/50 last:border-0 hover:bg-slate-700/20 transition-colors"
                      >
                        <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                          <div className="flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(entry.timestamp).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-300 max-w-[180px]">
                          <span className="truncate block" title={entry.filename}>
                            {entry.filename}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
                            <Icon className="w-3 h-3" />
                            {cfg.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-300">
                          {entry.predicted_class}
                          {entry.demo_mode && (
                            <span className="ml-2 text-xs text-indigo-400">(demo)</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className={`font-bold ${cfg.color}`}>
                            {Math.round(entry.confidence * 100)}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <div className="w-14 h-14 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Clock className="w-7 h-7 text-slate-600" />
            </div>
            <h3 className="text-slate-400 font-medium mb-2">No scan history</h3>
            <p className="text-slate-500 text-sm mb-6">
              Your analysis results will appear here after you run your first screening.
            </p>
            <Link
              to="/analysis"
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-sky-500 hover:bg-sky-400 text-white font-semibold rounded-xl transition-colors text-sm"
            >
              <Upload className="w-4 h-4" />
              Start First Analysis
            </Link>
          </motion.div>
        )}

        <p className="text-slate-600 text-xs text-center mt-6">
          History is stored locally in your browser and is never sent to any server.
        </p>
      </div>
    </div>
  )
}
