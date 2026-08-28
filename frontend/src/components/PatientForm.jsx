import { useState, useEffect } from 'react'
import { User, Stethoscope, Hash, Sparkles, ChevronDown, ChevronUp, UserCheck } from 'lucide-react'

const DOCTOR_PRESETS = [
  'Dr. Arjun Reddy — Orthopedic Specialist',
  'Dr. Karthik Rao — Radiologist',
  'Dr. Ananya Reddy — Radiologist',
  'Dr. Lee Felix — Sports Medicine & Joint Care',
  'Other (Custom Doctor Name)'
]

export default function PatientForm({ patientInfo, setPatientInfo }) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedDoctorOption, setSelectedDoctorOption] = useState(
    DOCTOR_PRESETS.includes(patientInfo.physician) ? patientInfo.physician : DOCTOR_PRESETS[0]
  )
  const [customDoctor, setCustomDoctor] = useState(
    DOCTOR_PRESETS.includes(patientInfo.physician) ? '' : (patientInfo.physician || '')
  )

  useEffect(() => {
    if (!patientInfo.id) {
      const autoId = 'BV-' + Math.floor(100000 + Math.random() * 900000)
      setPatientInfo((prev) => ({ 
        ...prev, 
        id: autoId, 
        name: prev.name || 'Suresh Kumar',
        age: prev.age || '54',
        gender: prev.gender || 'Male',
        kneeSide: prev.kneeSide || 'Right Knee (AP View)',
        physician: selectedDoctorOption,
        notes: prev.notes || 'Joint stiffness, suspected knee osteoarthritis'
      }))
    }
  }, [])

  function handleDoctorSelect(val) {
    setSelectedDoctorOption(val)
    if (val !== 'Other (Custom Doctor Name)') {
      setPatientInfo((prev) => ({ ...prev, physician: val }))
    } else {
      setPatientInfo((prev) => ({ ...prev, physician: customDoctor || '' }))
    }
  }

  function handleCustomDoctorChange(val) {
    setCustomDoctor(val)
    setPatientInfo((prev) => ({ ...prev, physician: val }))
  }

  function generateNewId() {
    const autoId = 'BV-' + Math.floor(100000 + Math.random() * 900000)
    setPatientInfo((prev) => ({ ...prev, id: autoId }))
  }

  return (
    <div className="bg-gradient-to-r from-slate-900/90 via-slate-800/80 to-slate-900/90 border border-slate-700/80 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md mb-6 transition-all">
      {/* Sleek Compact Header bar */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="px-5 py-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-700/30 transition-colors select-none"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">Patient Case</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                {patientInfo.id || 'BV-849201'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {patientInfo.name || 'Suresh Kumar'} ({patientInfo.age || '54'}y, {patientInfo.gender || 'Male'}) • {patientInfo.physician?.split('—')[0]?.trim() || 'Dr. Arjun Reddy'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-sky-400 font-medium hidden sm:inline">
            {isOpen ? 'Collapse Form' : 'Edit Patient & Doctor'}
          </span>
          <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* Expanded Modern Grid Form */}
      {isOpen && (
        <div className="p-5 pt-2 border-t border-slate-700/60 bg-slate-900/60 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-end">
            <button
              type="button"
              onClick={generateNewId}
              className="text-[11px] text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1 bg-sky-500/10 px-2.5 py-1 rounded-lg border border-sky-500/20 transition-colors"
            >
              <Hash className="w-3 h-3" />
              Generate New ID
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Patient ID */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Patient ID / MRN</label>
              <input
                type="text"
                value={patientInfo.id || ''}
                onChange={(e) => setPatientInfo({ ...patientInfo, id: e.target.value })}
                placeholder="BV-829104"
                className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            {/* Patient Name */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Patient Name</label>
              <input
                type="text"
                value={patientInfo.name || ''}
                onChange={(e) => setPatientInfo({ ...patientInfo, name: e.target.value })}
                placeholder="Suresh Kumar"
                className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>

            {/* Age & Gender */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Age</label>
                <input
                  type="number"
                  value={patientInfo.age || ''}
                  onChange={(e) => setPatientInfo({ ...patientInfo, age: e.target.value })}
                  placeholder="54"
                  className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Gender</label>
                <select
                  value={patientInfo.gender || 'Male'}
                  onChange={(e) => setPatientInfo({ ...patientInfo, gender: e.target.value })}
                  className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            {/* Knee Joint Side */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Knee Exam View</label>
              <select
                value={patientInfo.kneeSide || 'Right Knee (AP View)'}
                onChange={(e) => setPatientInfo({ ...patientInfo, kneeSide: e.target.value })}
                className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              >
                <option value="Right Knee (AP View)">Right Knee (AP View)</option>
                <option value="Left Knee (AP View)">Left Knee (AP View)</option>
                <option value="Bilateral Knee">Bilateral Knee</option>
              </select>
            </div>

            {/* Doctor Selection */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Stethoscope className="w-3.5 h-3.5 text-sky-400" />
                Attending Doctor
              </label>
              <select
                value={selectedDoctorOption}
                onChange={(e) => handleDoctorSelect(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
              >
                {DOCTOR_PRESETS.map((doc) => (
                  <option key={doc} value={doc}>
                    {doc}
                  </option>
                ))}
              </select>
            </div>

            {/* Custom Doctor Input OR Clinical Symptoms */}
            {selectedDoctorOption === 'Other (Custom Doctor Name)' ? (
              <div>
                <label className="block text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1">Custom Doctor Name</label>
                <input
                  type="text"
                  value={customDoctor}
                  onChange={(e) => handleCustomDoctorChange(e.target.value)}
                  placeholder="e.g. Dr. Cha Eun-woo / Dr. R. Murthy"
                  className="w-full bg-slate-800/80 border border-amber-500/60 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                />
              </div>
            ) : (
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Clinical Indication</label>
                <input
                  type="text"
                  value={patientInfo.notes || ''}
                  onChange={(e) => setPatientInfo({ ...patientInfo, notes: e.target.value })}
                  placeholder="e.g. Knee joint stiffness, weight-bearing pain"
                  className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>
            )}
          </div>

          {selectedDoctorOption === 'Other (Custom Doctor Name)' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Clinical Indication / Symptoms</label>
              <input
                type="text"
                value={patientInfo.notes || ''}
                onChange={(e) => setPatientInfo({ ...patientInfo, notes: e.target.value })}
                placeholder="e.g. Knee joint stiffness, weight-bearing pain"
                className="w-full bg-slate-800/80 border border-slate-700/90 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
