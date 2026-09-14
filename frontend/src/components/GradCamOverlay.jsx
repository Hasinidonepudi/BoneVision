import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Eye, Info, Sliders, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'

export default function GradCamOverlay({ file, heatmapBase64 }) {
  const [opacity, setOpacity] = useState(0.65)
  const [zoom, setZoom] = useState(1.0)
  const originalUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])

  function resetView() {
    setOpacity(0.65)
    setZoom(1.0)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-slate-800/90 rounded-2xl border border-slate-700/80 p-5 shadow-xl backdrop-blur-md"
    >
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-sky-400" />
          <h4 className="text-slate-200 font-semibold text-sm uppercase tracking-wider">
            Clinical Visual Explainability (Grad-CAM)
          </h4>
        </div>
        {heatmapBase64 && (
          <button
            onClick={resetView}
            className="text-[11px] text-slate-400 hover:text-sky-400 flex items-center gap-1 bg-slate-700/40 px-2.5 py-1 rounded-lg border border-slate-600/40 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Reset View
          </button>
        )}
      </div>

      {heatmapBase64 ? (
        <div>
          {/* Interactive Viewer Controls */}
          <div className="bg-slate-900/80 border border-slate-700/70 rounded-xl p-3 mb-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Opacity Slider */}
            <div className="flex items-center gap-3">
              <Sliders className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <div className="flex-1">
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Heatmap Opacity</span>
                  <span className="font-mono text-sky-300">{Math.round(opacity * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={opacity}
                  onChange={(e) => setOpacity(parseFloat(e.target.value))}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-400"
                />
              </div>
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center justify-between sm:justify-end gap-3">
              <span className="text-[11px] text-slate-400">Zoom: <span className="font-mono text-sky-300">{Math.round(zoom * 100)}%</span></span>
              <div className="flex items-center gap-1.5 bg-slate-800 p-1 rounded-lg border border-slate-700">
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.max(0.8, z - 0.2))}
                  className="p-1 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setZoom((z) => Math.min(2.2, z + 0.2))}
                  className="p-1 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Side by Side Inspection Panes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: Original Scan */}
            <div className="bg-black/60 rounded-xl p-2 border border-slate-700/60 overflow-hidden flex flex-col items-center">
              <p className="text-slate-400 text-xs mb-2 font-medium">Original Diagnostic Knee X-Ray</p>
              <div className="w-full h-56 flex items-center justify-center overflow-hidden rounded-lg">
                {originalUrl && (
                  <img
                    src={originalUrl}
                    alt="Original X-ray"
                    style={{ transform: `scale(${zoom})`, transition: 'transform 0.15s ease-out' }}
                    className="max-h-52 object-contain grayscale"
                  />
                )}
              </div>
            </div>

            {/* Right: Interactive Blended Heatmap */}
            <div className="bg-black/60 rounded-xl p-2 border border-slate-700/60 overflow-hidden flex flex-col items-center">
              <p className="text-slate-400 text-xs mb-2 font-medium">Interactive Trabecular Attention Overlay</p>
              <div className="w-full h-56 flex items-center justify-center overflow-hidden rounded-lg relative">
                {/* Base grayscale X-ray */}
                {originalUrl && (
                  <img
                    src={originalUrl}
                    alt="Base X-ray"
                    style={{ transform: `scale(${zoom})`, transition: 'transform 0.15s ease-out' }}
                    className="max-h-52 object-contain grayscale absolute"
                  />
                )}
                {/* Heatmap overlay with dynamic opacity */}
                <img
                  src={`data:image/png;base64,${heatmapBase64}`}
                  alt="Grad-CAM overlay"
                  style={{
                    opacity: opacity,
                    transform: `scale(${zoom})`,
                    transition: 'transform 0.15s ease-out, opacity 0.1s ease',
                  }}
                  className="max-h-52 object-contain mix-blend-screen"
                />
              </div>
            </div>
          </div>

          <p className="text-slate-500 text-[11px] mt-3 text-center">
            🔥 Warmer colors (Red/Orange) focus on subchondral bone density loss & tibial joint space narrowing.
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-10 text-center gap-3 bg-slate-900/50 rounded-xl">
          <div className="w-12 h-12 bg-slate-700/50 rounded-xl flex items-center justify-center">
            <Info className="w-6 h-6 text-slate-500" />
          </div>
          <div>
            <p className="text-slate-400 font-medium">Explainability Visualization</p>
            <p className="text-slate-500 text-sm mt-1">Available after running model analysis.</p>
          </div>
        </div>
      )}
    </motion.div>
  )
}
