import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Activity, Zap, Eye, ShieldCheck, ChevronRight,
  Bone, AlertTriangle, TrendingDown,
} from 'lucide-react'

const FEATURES = [
  {
    icon: Zap,
    title: 'Fast Analysis',
    desc: 'AI inference in under 2 seconds. Instant screening results with confidence scores.',
    color: 'text-sky-400',
    bg: 'bg-sky-500/10',
  },
  {
    icon: Eye,
    title: 'Explainability',
    desc: 'Grad-CAM attention maps highlight the exact knee regions that influenced the prediction.',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10',
  },
  {
    icon: ShieldCheck,
    title: 'Safe by Design',
    desc: 'Uncertain results are flagged for manual review. No forced predictions below confidence threshold.',
    color: 'text-green-400',
    bg: 'bg-green-500/10',
  },
]

const CLASSES = [
  {
    icon: Bone,
    label: 'Normal',
    desc: 'Healthy bone density and joint structure. No significant abnormalities detected.',
    color: 'text-green-400',
    border: 'border-green-500/30',
    bg: 'bg-green-500/5',
  },
  {
    icon: TrendingDown,
    label: 'Osteopenia',
    desc: 'Reduced bone density — a pre-osteoporosis state. Requires monitoring and lifestyle interventions.',
    color: 'text-amber-400',
    border: 'border-amber-500/30',
    bg: 'bg-amber-500/5',
  },
  {
    icon: AlertTriangle,
    label: 'Osteoporosis',
    desc: 'Significantly reduced bone density with elevated fracture risk. Clinical intervention recommended.',
    color: 'text-red-400',
    border: 'border-red-500/30',
    bg: 'bg-red-500/5',
  },
]

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay },
})

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative pt-32 pb-20 px-4 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-b from-sky-900/10 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div {...fade(0.1)} className="inline-flex items-center gap-2 px-4 py-1.5 bg-sky-500/10 border border-sky-500/30 rounded-full text-sky-400 text-sm font-medium mb-6">
            <Activity className="w-4 h-4" />
            AI-Assisted Screening · Research Prototype
          </motion.div>

          <motion.h1 {...fade(0.2)} className="text-5xl md:text-6xl font-bold text-slate-100 mb-6 leading-tight">
            AI-Assisted Knee
            <br />
            <span className="gradient-text">Osteoporosis Screening</span>
          </motion.h1>

          <motion.p {...fade(0.3)} className="text-slate-400 text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
            Upload a knee X-ray for instant AI screening of{' '}
            <span className="text-green-400 font-medium">Normal</span>,{' '}
            <span className="text-amber-400 font-medium">Osteopenia</span>, and{' '}
            <span className="text-red-400 font-medium">Osteoporosis</span> patterns using
            transfer learning with explainability visualisation.
          </motion.p>

          <motion.div {...fade(0.4)} className="flex flex-wrap gap-4 justify-center">
            <Link
              to="/analysis"
              className="flex items-center gap-2 px-8 py-3.5 bg-sky-500 hover:bg-sky-400 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-sky-500/20"
            >
              Start Screening
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/dashboard"
              className="flex items-center gap-2 px-8 py-3.5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold rounded-xl transition-colors"
            >
              View Dashboard
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 border-t border-slate-800">
        <div className="max-w-5xl mx-auto">
          <motion.h2 {...fade(0.1)} className="text-2xl font-bold text-slate-200 text-center mb-10">
            Clinically Responsible AI
          </motion.h2>
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div key={f.title} {...fade(0.2 + i * 0.1)}
                className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 hover:border-slate-600 transition-colors"
              >
                <div className={`w-11 h-11 ${f.bg} rounded-xl flex items-center justify-center mb-4`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="text-slate-200 font-semibold mb-2">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Conditions */}
      <section className="py-16 px-4 border-t border-slate-800">
        <div className="max-w-5xl mx-auto">
          <motion.h2 {...fade(0.1)} className="text-2xl font-bold text-slate-200 text-center mb-2">
            Detected Conditions
          </motion.h2>
          <motion.p {...fade(0.15)} className="text-slate-500 text-center text-sm mb-10">
            The model is trained to classify only these three categories.
          </motion.p>
          <div className="grid md:grid-cols-3 gap-6">
            {CLASSES.map((c, i) => (
              <motion.div key={c.label} {...fade(0.2 + i * 0.1)}
                className={`rounded-2xl border p-6 ${c.bg} ${c.border}`}
              >
                <div className={`w-10 h-10 bg-slate-800/50 rounded-xl flex items-center justify-center mb-4`}>
                  <c.icon className={`w-5 h-5 ${c.color}`} />
                </div>
                <h3 className={`font-bold text-lg mb-2 ${c.color}`}>{c.label}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{c.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-12 px-4 border-t border-slate-800 bg-slate-900/50">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-amber-400 mb-3">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">Important Medical Disclaimer</span>
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">
            BoneVision is a <strong className="text-slate-300">research prototype</strong> and
            AI-assisted decision-support tool. It is <strong className="text-red-400">NOT</strong> a
            substitute for clinical diagnosis. All results must be interpreted and confirmed by a
            qualified radiologist or healthcare professional. This tool has not been approved by any
            medical regulatory authority and should not be used as the sole basis for clinical decisions.
          </p>
        </div>
      </section>
    </div>
  )
}
