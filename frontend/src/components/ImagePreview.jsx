import { useMemo } from 'react'
import { FileImage } from 'lucide-react'

export default function ImagePreview({ file, className = '' }) {
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  if (!file || !url) return null

  const sizeKB = (file.size / 1024).toFixed(1)

  return (
    <div className={`rounded-xl overflow-hidden bg-slate-800 border border-slate-700 ${className}`}>
      <div className="relative">
        <img
          src={url}
          alt="Uploaded X-ray"
          className="w-full object-contain max-h-72 grayscale"
        />
        <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 rounded-lg text-xs text-slate-300">
          Preview
        </div>
      </div>
      <div className="px-4 py-3 flex items-center gap-2 text-slate-400 text-sm border-t border-slate-700">
        <FileImage className="w-4 h-4 shrink-0" />
        <span className="truncate font-medium text-slate-300">{file.name}</span>
        <span className="ml-auto shrink-0">{sizeKB} KB</span>
      </div>
    </div>
  )
}
