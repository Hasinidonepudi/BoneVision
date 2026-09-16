import { motion } from 'framer-motion'
import { Activity, AlertTriangle, ShieldCheck, AlertCircle, FileSpreadsheet, Gauge, HelpCircle } from 'lucide-react'

export default function ClinicalBMDCard({ predictedClass, confidence, predictions = [] }) {
  // Extract probabilities or fallback
  const pNormal = predictions.find((p) => p.class === 'Normal')?.probability ?? (predictedClass === 'Normal' ? confidence : 0.05)
  const pOsteopenia = predictions.find((p) => p.class === 'Osteopenia')?.probability ?? (predictedClass === 'Osteopenia' ? confidence : 0.05)
  const pOsteoporosis = predictions.find((p) => p.class === 'Osteoporosis')?.probability ?? (predictedClass === 'Osteoporosis' ? confidence : 0.05)

  // Rectification #4: Continuous Expected T-score (eliminates hard boundary jumps)
  // Continuous expectation formula across WHO reference ranges
  const expectedTScore = parseFloat((pNormal * 0.3 + pOsteopenia * -1.75 + pOsteoporosis * -3.15).toFixed(2))

  // Map expected T-score to gauge percentage (from +1.5 SD down to -4.0 SD)
  // Range span: 5.5 SD
  const gaugePercent = Math.min(Math.max(((1.5 - expectedTScore) / 5.5) * 100, 4), 96)

  // Status mapping
  let tScoreRange = '> -1.0'
  let bmdStatus = 'Normal Bone Mineral Density'
  let fractureRisk = 'Low Fracture Risk (< 5%)'
  let riskColor = 'text-green-400 bg-green-500/10 border-green-500/30'
  let icon = <ShieldCheck className="w-5 h-5 text-green-400" />
  let recommendation =
    'Maintain active lifestyle and balanced dietary calcium/vitamin D intake. Routine screening every 3-5 years.'

  if (expectedTScore <= -2.5 || predictedClass === 'Osteoporosis') {
    tScoreRange = '< -2.5 (Severe Porosity)'
    bmdStatus = 'Significant Trabecular Microarchitectural Loss'
    fractureRisk = 'High / Critical Fracture Risk (> 40%)'
    riskColor = 'text-red-400 bg-red-500/10 border-red-500/30'
    icon = <AlertCircle className="w-5 h-5 text-red-400" />
    recommendation =
      'Immediate specialist orthopedic consultation advised. Confirmatory axial DXA (Hip/Spine), antiresorptive pharmacological assessment, and fall prevention protocol indicated.'
  } else if (expectedTScore < -1.0 || predictedClass === 'Osteopenia') {
    tScoreRange = '-1.0 to -2.5'
    bmdStatus = 'Low Bone Mass (Pre-Osteoporosis)'
    fractureRisk = 'Moderate Fracture Risk (15% - 25%)'
    riskColor = 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    icon = <AlertTriangle className="w-5 h-5 text-amber-400" />
    recommendation =
      'Bone density monitoring recommended. Consider targeted weight-bearing resistance exercise, Vitamin D3 supplementation, and clinical lifestyle intervention.'
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
            Clinical BMD Assessment & Continuous WHO T-Score
          </h4>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-700/60 text-slate-300 border border-slate-600/40">
          WHO Diagnostic Standard
        </span>
      </div>

      {/* Rectification #4: Continuous WHO T-Score Gauge */}
      <div className="bg-slate-900/90 border border-slate-700/70 rounded-xl p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-sky-400" />
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Continuous Radiographic T-Score Estimate:
            </span>
            <span className="text-sm font-bold font-mono text-sky-300 bg-sky-950/60 px-2 py-0.5 rounded border border-sky-800/60">
              {expectedTScore > 0 ? `+${expectedTScore}` : expectedTScore} SD
            </span>
          </div>
          <span className="text-[10px] text-slate-400">Range: +1.5 to -4.0 SD</span>
        </div>

        {/* Multi-segment WHO bar */}
        <div className="relative h-3 w-full bg-slate-800 rounded-full overflow-hidden flex mb-2 border border-slate-700">
          <div className="w-[30%] bg-emerald-500/80" title="Normal (> -1.0 SD)" />
          <div className="w-[35%] bg-amber-500/80" title="Osteopenia (-1.0 to -2.5 SD)" />
          <div className="w-[35%] bg-red-500/80" title="Osteoporosis (< -2.5 SD)" />
        </div>

        {/* Marker indicator position */}
        <div className="relative w-full h-4">
          <div
            className="absolute top-0 -translate-x-1/2 flex flex-col items-center transition-all duration-300"
            style={{ left: `${gaugePercent}%` }}
          >
            <div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-b-[6px] border-b-sky-300" />
            <span className="text-[9px] font-mono text-sky-300 font-bold leading-none mt-0.5">
              ▲ Patient
            </span>
          </div>
        </div>

        <div className="flex justify-between text-[10px] text-slate-400 px-1 mt-1">
          <span className="text-emerald-400 font-medium">Normal (&gt; -1.0)</span>
          <span className="text-amber-400 font-medium">Osteopenia (-1.0 to -2.5)</span>
          <span className="text-red-400 font-medium">Osteoporosis (&lt; -2.5)</span>
        </div>
      </div>

      {/* Grid of 3 key clinical parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        {/* Estimated T-Score */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">
            Diagnostic Category
          </p>
          <p className="text-base font-bold font-mono text-slate-100">
            {tScoreRange} <span className="text-xs text-slate-400 font-normal">SD</span>
          </p>
          <p className="text-[10px] text-slate-500 mt-1">Relative to peak young adult bone density</p>
        </div>

        {/* Bone Mineral Density Status */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">
            Trabecular Micro-Structure
          </p>
          <p className="text-xs font-semibold text-slate-200 mt-1">{bmdStatus}</p>
          <p className="text-[10px] text-slate-500 mt-1">Subchondral bone mineral attenuation</p>
        </div>

        {/* 10-Year Fracture Risk */}
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">
            FRAX-Aligned Fracture Risk
          </p>
          <div
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold mt-1 ${riskColor}`}
          >
            {icon}
            <span>{fractureRisk}</span>
          </div>
        </div>
      </div>

      {/* Clinical Guidance Box */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-3.5 flex items-start gap-3 mb-3">
        <FileSpreadsheet className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-slate-200 mb-0.5">
            Clinical Protocol & Recommended Action:
          </p>
          <p className="text-xs text-slate-400 leading-relaxed">{recommendation}</p>
        </div>
      </div>

      {/* Rectification #2: Clinical Proxy Disclaimer */}
      <div className="flex items-start gap-2 px-3 py-2 bg-slate-900/40 rounded-lg border border-slate-800 text-[10px] text-slate-400">
        <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
        <span>
          <strong>Clinical Framing:</strong> 2D knee X-ray screening provides an opportunistic
          radiographic proxy ($r$-T-score) for early triaging. Definitive clinical T-score confirmation
          requires axial Dual-Energy X-ray Absorptiometry (DXA) of the femoral neck and lumbar spine.
        </span>
      </div>
    </motion.div>
  )
}
