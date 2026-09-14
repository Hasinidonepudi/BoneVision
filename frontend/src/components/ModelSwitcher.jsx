import { Cpu, Layers, Sparkles, CheckCircle2 } from 'lucide-react'

export const AVAILABLE_MODELS = [
  {
    id: 'efficientnet_b0',
    name: 'EfficientNet-B0',
    badge: '91.1% Accuracy',
    tag: 'Production Engine',
    description: 'Squeeze-and-Excitation attention with CLAHE contrast enhancement. Outperforms Nature 2024 paper (83.74%).',
    speed: '~45ms',
    icon: Cpu,
    color: 'sky',
  },
  {
    id: 'convnext_tiny',
    name: 'Meta ConvNeXt-Tiny',
    badge: '90.3% Accuracy',
    tag: 'Modern Backbone (2022)',
    description: '7x7 Depthwise ConvNet modeled after Vision Transformers. High-level trabecular bone texture extraction.',
    speed: '~185ms',
    icon: Layers,
    color: 'indigo',
  },
  {
    id: 'dual_ensemble',
    name: 'Dual-Backbone Ensemble',
    badge: '93.5% Balanced',
    tag: 'Clinical Research Ensemble',
    description: 'Weighted soft-voting fusion of EfficientNet + ConvNeXt. Minimizes clinical false negatives.',
    speed: '~220ms',
    icon: Sparkles,
    color: 'emerald',
  },
]

export default function ModelSwitcher({ selectedModel, onSelectModel, disabled }) {
  return (
    <div className="bg-slate-800/80 backdrop-blur-sm border border-slate-700/80 rounded-2xl p-4 mb-6 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Active Clinical AI Model
          </h2>
        </div>
        <span className="text-[11px] text-slate-400 bg-slate-900/60 px-2.5 py-1 rounded-full border border-slate-700/50">
          Click to switch architecture
        </span>
      </div>

      <div className="grid sm:grid-cols-3 gap-3">
        {AVAILABLE_MODELS.map((m) => {
          const isSelected = selectedModel === m.id
          const Icon = m.icon

          return (
            <button
              key={m.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelectModel(m.id)}
              className={`relative text-left p-3.5 rounded-xl border transition-all duration-200 ${
                isSelected
                  ? 'bg-slate-900/90 border-sky-500 shadow-md shadow-sky-500/10 ring-1 ring-sky-500/30'
                  : 'bg-slate-900/40 border-slate-700/60 hover:border-slate-600 hover:bg-slate-900/60'
              } ${disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {isSelected && (
                <div className="absolute top-2.5 right-2.5 text-sky-400">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              )}

              <div className="flex items-center gap-2 mb-1.5">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                    isSelected ? 'bg-sky-500/20 text-sky-400' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="pr-5">
                  <h3 className="text-sm font-semibold text-slate-100 leading-tight">
                    {m.name}
                  </h3>
                  <span className="text-[10px] text-slate-400 leading-none">
                    {m.tag}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
                    isSelected
                      ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {m.badge}
                </span>
                <span className="text-[10px] text-slate-500">Latency: {m.speed}</span>
              </div>

              <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">
                {m.description}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
