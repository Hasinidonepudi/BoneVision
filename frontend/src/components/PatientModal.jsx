import { useState } from 'react'
import { User, FileText, Download, X } from 'lucide-react'

export default function PatientModal({ isOpen, onClose, onExport }) {
  const [info, setInfo] = useState({
    name: '',
    id: '',
    age: '',
    gender: 'Male',
    physician: '',
    notes: '',
  })

  if (!isOpen) return null

  function handleSubmit(e) {
    e.preventDefault()
    onExport(info)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-sky-400" />
            <h3 className="text-lg font-bold text-slate-100">Patient & Report Details</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Patient Name</label>
              <input
                type="text"
                value={info.name}
                onChange={(e) => setInfo({ ...info, name: e.target.value })}
                placeholder="e.g. John Doe"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Patient ID / MRN</label>
              <input
                type="text"
                value={info.id}
                onChange={(e) => setInfo({ ...info, id: e.target.value })}
                placeholder="e.g. MRN-84920"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Age</label>
              <input
                type="number"
                value={info.age}
                onChange={(e) => setInfo({ ...info, age: e.target.value })}
                placeholder="e.g. 58"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Gender</label>
              <select
                value={info.gender}
                onChange={(e) => setInfo({ ...info, gender: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Referring Physician</label>
            <input
              type="text"
              value={info.physician}
              onChange={(e) => setInfo({ ...info, physician: e.target.value })}
              placeholder="e.g. Dr. Rajesh Sharma, MD"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Clinical Notes / Indications</label>
            <textarea
              rows="3"
              value={info.notes}
              onChange={(e) => setInfo({ ...info, notes: e.target.value })}
              placeholder="e.g. Bilateral knee joint pain for 6 months, history of osteopenia."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-sky-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 px-5 py-2 bg-sky-500 hover:bg-sky-400 text-white rounded-xl text-sm font-semibold transition-colors shadow-lg shadow-sky-500/20"
            >
              <Download className="w-4 h-4" />
              Download Clinical Report (PDF)
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
