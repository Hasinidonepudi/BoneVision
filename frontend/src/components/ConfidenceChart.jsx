import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const CLASS_COLORS = {
  Normal: '#22c55e',
  Osteopenia: '#f59e0b',
  Osteoporosis: '#ef4444',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div className="bg-slate-800 border border-slate-700 px-3 py-2 rounded-lg text-sm">
      <p className="text-slate-300 font-medium">{name}</p>
      <p className="text-slate-400">{(value * 100).toFixed(1)}%</p>
    </div>
  )
}

export default function ConfidenceChart({ predictions }) {
  if (!predictions?.length) return null

  const data = predictions.map((p) => ({
    name: p.class,
    value: p.probability,
  }))

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-slate-800 rounded-2xl border border-slate-700 p-5"
    >
      <h4 className="text-slate-300 font-semibold mb-4 text-sm uppercase tracking-wider">
        Class Probabilities
      </h4>

      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20, top: 0, bottom: 0 }}>
          <XAxis
            type="number"
            domain={[0, 1]}
            tickFormatter={(v) => `${Math.round(v * 100)}%`}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#cbd5e1', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={90}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={CLASS_COLORS[entry.name] || '#6366f1'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex gap-4 mt-3 justify-center flex-wrap">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5 text-xs text-slate-400">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: CLASS_COLORS[d.name] || '#6366f1' }}
            />
            {d.name}: {(d.value * 100).toFixed(1)}%
          </div>
        ))}
      </div>
    </motion.div>
  )
}
