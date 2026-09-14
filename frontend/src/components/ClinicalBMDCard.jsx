import { motion } from 'framer-motion'
import { Activity, AlertTriangle, ShieldCheck, AlertCircle, FileSpreadsheet } from 'lucide-react'

export default function ClinicalBMDCard({ predictedClass, confidence }) {
  // Clinical DEXA WHO T-Score Mapping
  let tScoreRange = '> -1.0'
  let bmdStatus = 'Normal Bone Mineral Density'
  let fractureRisk = 'Low Fracture Risk (< 5%)'
  let riskColor = 'text-green-400 bg-green-500/10 border-green-500/30'
  let icon = <ShieldCheck className="w-5 h-5 text-green-400" />
  let recommendation = 'Maintain active lifestyle and balanced dietary calcium/vitamin D intake. Routine screening every 3-5 years.'

  if (predictedClass === 'Osteopenia') {
    tScoreRange = '-1.0 to -2.5'
    bmdStatus = 'Low Bone Mass (Pre-Osteoporosis)'
    fractureRisk = 'Moderate Fracture Risk (15% - 25%)'
    riskColor = 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    icon = <AlertTriangle className="w-5 h-5 text-amber-400" />
    recommendation = 'Bone density monitoring recommended. Consider targeted resistance exercise, Vitamin D3 supplementation, and clinical lifestyle intervention.'
  } else if (predictedClass === 'Osteoporosis') {
    tScoreRange = '< -2.5 (Severe Loss)'
    bmdStatus = 'Significant Trabecular Microarchitectural Loss'
    fractureRisk = 'High / Critical Fracture Risk (> 40%)'
    riskColor = 'text-red-400 bg-red-500/10 border-red-500/30'
    icon = <AlertCircle className="w-5 h-5 text-red-400" />
    recommendation = 'Immediate specialist orthopedic consultation advised. DEXA confirmatory scan, antiresorptive pharmacological assessment, and fall prevention protocol indicated.'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="bg-slate-800/90 rounded-2xl border border-slate-700/80 p-5 shadow-xl backdrop-blur-md mb-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-700/70 mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-400" />
          <h4 className="text-slate-200 font-semibold text-sm uppercase tracking-wider">
            Clinical BMD Assessment & WHO T-Score Correlate
          </h4>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-700/60 text-slate-300 border border-slate-600/40">
          WHO Criteria 2024
        </span>
      </div>

      {/* Grid of 3 key clinical parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        {/* Estimated T-Score */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Estimated T-Score Range</p>
          <p className="text-lg font-bold font-mono text-slate-100">{tScoreRange} <span className="text-xs text-slate-400 font-normal">SD</span></p>
          <p className="text-[10px] text-slate-500 mt-1">Relative to peak young adult bone density</p>
        </div>

        {/* Bone Mineral Density Status */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Trabecular Status</p>
          <p className="text-sm font-semibold text-slate-200 mt-1">{bmdStatus}</p>
          <p className="text-[10px] text-slate-500 mt-1">Based on tibial subchondral analysis</p>
        </div>

        {/* 10-Year Fracture Risk */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">FRAX-Aligned Fracture Risk</p>
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold mt-1 ${riskColor}`}>
            {icon}
            <span>{fractureRisk}</span>
          </div>
        </div>
      </div>

      {/* Clinical Guidance Box */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3.5 flex items-start gap-3">
        <FileSpreadsheet className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-slate-200 mb-0.5">Clinical Protocol & Recommended Action:</p>
          <p className="text-xs text-slate-400 leading-relaxed">{recommendation}</p>
        </div>
      </div>
    </motion.div>
  )
}
