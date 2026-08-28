import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Eye, Info } from 'lucide-react'

export default function GradCamOverlay({ file, heatmapBase64 }) {
  const originalUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-slate-800 rounded-2xl border border-slate-700 p-5"
    >
      <div className="flex items-center gap-2 mb-4">
        <Eye className="w-4 h-4 text-indigo-400" />
        <h4 className="text-slate-300 font-semibold text-sm uppercase tracking-wider">
          Explainability — Grad-CAM
        </h4>
      </div>

      {heatmapBase64 ? (
        <div className="grid grid-cols-2 gap-3">
          {/* Original */}
          <div>
            <p className="text-slate-500 text-xs mb-2 text-center">Original X-ray</p>
            {originalUrl && (
              <img
                src={originalUrl}
                alt="Original X-ray"
                className="w-full rounded-lg object-contain max-h-52 grayscale bg-black"
              />
            )}
          </div>
          {/* Heatmap overlay */}
          <div>
            <p className="text-slate-500 text-xs mb-2 text-center">Activation Heatmap</p>
            <img
              src={`data:image/png;base64,${heatmapBase64}`}
              alt="Grad-CAM heatmap"
              className="w-full rounded-lg object-contain max-h-52 bg-black"
            />
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-10 text-center gap-3 bg-slate-900/50 rounded-xl">
          <div className="w-12 h-12 bg-slate-700/50 rounded-xl flex items-center justify-center">
            <Info className="w-6 h-6 text-slate-500" />
          </div>
          <div>
            <p className="text-slate-400 font-medium">Explainability Visualization</p>
            <p className="text-slate-500 text-sm mt-1">
              Available after running the trained model.
            </p>
            <p className="text-slate-600 text-xs mt-2">
              Grad-CAM highlights the knee regions that influenced the prediction.
            </p>
          </div>
        </div>
      )}

      <p className="text-slate-600 text-xs mt-3 text-center">
        Warmer colours (red/orange) indicate regions of higher model attention.
      </p>
    </motion.div>
  )
}
