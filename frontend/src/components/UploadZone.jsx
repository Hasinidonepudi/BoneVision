import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'
import { CloudUpload, ImageIcon, AlertCircle } from 'lucide-react'

const MAX_SIZE = 10 * 1024 * 1024 // 10 MB
const ACCEPTED = { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'] }

export default function UploadZone({ onFileSelect, disabled }) {
  const onDrop = useCallback(
    (accepted) => {
      if (accepted.length > 0 && onFileSelect) onFileSelect(accepted[0])
    },
    [onFileSelect]
  )

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    maxFiles: 1,
    disabled,
  })

  const rejection = fileRejections[0]
  const errorMsg = rejection
    ? rejection.errors[0]?.code === 'file-too-large'
      ? 'File exceeds 10 MB limit.'
      : rejection.errors[0]?.code === 'file-invalid-type'
      ? 'Only JPEG and PNG images are accepted.'
      : rejection.errors[0]?.message
    : null

  return (
    <div className="w-full">
      <motion.div
        {...getRootProps()}
        whileHover={!disabled ? { scale: 1.01 } : {}}
        className={`
          relative rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer
          transition-all duration-200
          ${disabled ? 'opacity-50 cursor-not-allowed border-slate-700 bg-slate-800/30' : ''}
          ${isDragActive
            ? 'border-sky-400 bg-sky-500/10 shadow-[0_0_30px_rgba(14,165,233,0.2)]'
            : !disabled
            ? 'border-slate-600 bg-slate-800/50 hover:border-sky-500 hover:bg-sky-500/5'
            : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          <motion.div
            animate={isDragActive ? { scale: 1.2, rotate: 5 } : { scale: 1, rotate: 0 }}
            className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
              isDragActive ? 'bg-sky-500/20' : 'bg-slate-700/50'
            }`}
          >
            {isDragActive ? (
              <ImageIcon className="w-8 h-8 text-sky-400" />
            ) : (
              <CloudUpload className="w-8 h-8 text-slate-400" />
            )}
          </motion.div>

          <div>
            <p className="text-slate-200 font-semibold text-lg mb-1">
              {isDragActive ? 'Drop your X-ray here' : 'Drag & drop your knee X-ray'}
            </p>
            <p className="text-slate-400 text-sm">
              or{' '}
              <span className="text-sky-400 font-medium">click to browse</span>
            </p>
          </div>

          <div className="flex gap-3 text-xs text-slate-500">
            <span className="px-2 py-1 bg-slate-700/50 rounded-full">JPEG</span>
            <span className="px-2 py-1 bg-slate-700/50 rounded-full">PNG</span>
            <span className="px-2 py-1 bg-slate-700/50 rounded-full">Max 10 MB</span>
          </div>
        </div>
      </motion.div>

      {errorMsg && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 flex items-center gap-2 text-red-400 text-sm"
        >
          <AlertCircle className="w-4 h-4 shrink-0" />
          {errorMsg}
        </motion.div>
      )}
    </div>
  )
}
