import { Routes, Route } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useLocation } from 'react-router-dom'

import Navbar from './components/Navbar'
import DisclaimerBanner from './components/DisclaimerBanner'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import History from './pages/History'

export default function App() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-slate-900">
      <Navbar />
      <DisclaimerBanner />

      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          <Routes location={location}>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/history" element={<History />} />
            <Route path="*" element={
              <div className="flex flex-col items-center justify-center min-h-screen gap-4">
                <p className="text-slate-300 text-2xl font-bold">404 — Page Not Found</p>
                <a href="/" className="text-sky-400 hover:underline">Go home</a>
              </div>
            } />
          </Routes>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
