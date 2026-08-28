import { useState, useEffect } from 'react'
import { AlertTriangle, X } from 'lucide-react'

const SESSION_KEY = 'bv_disclaimer_dismissed'

export default function DisclaimerBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const dismissed = sessionStorage.getItem(SESSION_KEY)
    if (!dismissed) setVisible(true)
  }, [])

  const dismiss = () => {
    sessionStorage.setItem(SESSION_KEY, '1')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/30 text-amber-300 text-sm px-4 py-2.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            <strong>AI Screening Tool</strong> — Not a substitute for professional medical diagnosis.
            Always consult a qualified radiologist before making clinical decisions.
          </span>
        </div>
        <button onClick={dismiss} className="shrink-0 hover:text-amber-100 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
