import { jsPDF } from 'jspdf'

/**
 * Generate and download a PDF medical screening report for BoneVision.
 */
export function generatePDFReport({ result, patientInfo, file, heatmapBase64 }) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const margin = 15
  let y = 15

  // Header Banner
  doc.setFillColor(15, 23, 42) // slate-900
  doc.rect(0, 0, pageWidth, 28, 'F')

  doc.setTextColor(14, 165, 233) // sky-500
  doc.setFontSize(20)
  doc.setFont('helvetica', 'bold')
  doc.text('BoneVision', margin, 12)

  doc.setTextColor(203, 213, 225) // slate-300
  doc.setFontSize(10)
  doc.setFont('helvetica', 'normal')
  doc.text('AI-Assisted Knee Osteoarthritis & Bone Density Screening Report', margin, 18)

  doc.setFontSize(8)
  doc.setTextColor(148, 163, 184) // slate-400
  const dateStr = new Date().toLocaleString()
  doc.text(`Generated: ${dateStr}`, pageWidth - margin - 50, 18)

  y = 35

  // Patient Info Box
  doc.setDrawColor(226, 232, 240)
  doc.setFillColor(248, 250, 252)
  doc.roundedRect(margin, y, pageWidth - 2 * margin, 28, 2, 2, 'FD')

  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 41, 59)
  doc.text('Patient & Study Details', margin + 4, y + 6)

  doc.setFontSize(9)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(71, 85, 105)

  const pName = patientInfo?.name || 'Anonymous'
  const pId = patientInfo?.id || 'BV-' + Math.floor(100000 + Math.random() * 900000)
  const pAge = patientInfo?.age ? `${patientInfo.age} yrs` : 'Not specified'
  const pGender = patientInfo?.gender || 'Not specified'
  const pPhysician = patientInfo?.physician || 'N/A'

  doc.text(`Patient Name: ${pName}`, margin + 4, y + 13)
  doc.text(`Patient ID: ${pId}`, margin + 65, y + 13)
  doc.text(`Age / Gender: ${pAge} / ${pGender}`, margin + 125, y + 13)

  doc.text(`Referring Doctor: ${pPhysician}`, margin + 4, y + 20)
  doc.text(`Image File: ${file?.name || 'xray.jpg'}`, margin + 65, y + 20)
  doc.text(`Model Version: ${result?.model_version || 'bonevision-v1.0'}`, margin + 125, y + 20)

  y += 34

  // Screening Result Box
  const statusColor =
    result.status === 'NORMAL' ? [34, 197, 94] :
    result.status === 'ABNORMAL' ? [245, 158, 11] : [100, 116, 139]

  doc.setDrawColor(statusColor[0], statusColor[1], statusColor[2])
  doc.setFillColor(statusColor[0], statusColor[1], statusColor[2])
  doc.roundedRect(margin, y, pageWidth - 2 * margin, 24, 2, 2, 'FD')

  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(255, 255, 255)
  doc.text('AI SCREENING CLASSIFICATION RESULT', margin + 5, y + 7)

  doc.setFontSize(14)
  doc.text(`${result.predicted_class?.toUpperCase()} (${Math.round((result.confidence || 0) * 100)}% Confidence)`, margin + 5, y + 16)

  const reviewTag = result.requires_review ? '⚠️ MANUAL SPECIALIST REVIEW REQUIRED' : '✓ Standard Screening'
  doc.setFontSize(9)
  doc.text(reviewTag, pageWidth - margin - 70, y + 16)

  y += 30

  // Probability Breakdown Table
  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 41, 59)
  doc.text('Class Probability Distribution', margin, y)

  y += 4
  if (result.predictions && result.predictions.length > 0) {
    result.predictions.forEach((p, idx) => {
      const probPct = Math.round(p.probability * 100)
      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(51, 65, 85)
      doc.text(`${p.class}:`, margin + 5, y + 6)
      doc.text(`${probPct}%`, margin + 45, y + 6)

      // Bar
      doc.setFillColor(226, 232, 240)
      doc.rect(margin + 58, y + 2.5, 100, 4, 'F')

      const barColor =
        p.class === 'Normal' ? [34, 197, 94] :
        p.class === 'Osteopenia' ? [245, 158, 11] : [239, 68, 68]
      doc.setFillColor(barColor[0], barColor[1], barColor[2])
      doc.rect(margin + 58, y + 2.5, probPct, 4, 'F')

      y += 8
    })
  }

  y += 6

  // Images Section: Original X-Ray and Heatmap
  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(30, 41, 59)
  doc.text('Diagnostic Imagery & AI Attention Map (Grad-CAM)', margin, y)

  y += 4
  const imgBoxWidth = 80
  const imgBoxHeight = 70

  // Heatmap image if available
  if (heatmapBase64) {
    try {
      doc.addImage(
        `data:image/png;base64,${heatmapBase64}`,
        'PNG',
        margin + 45,
        y,
        imgBoxWidth,
        imgBoxHeight
      )
      doc.setFontSize(8)
      doc.setTextColor(100, 116, 139)
      doc.text('Grad-CAM Heatmap Overlay (Red = High Attention)', margin + 45, y + imgBoxHeight + 5)
    } catch (e) {
      console.warn('Failed to add heatmap to PDF', e)
    }
  }

  y += imgBoxHeight + 12

  // Clinical Notes Box
  if (patientInfo?.notes) {
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(30, 41, 59)
    doc.text('Physician / Clinical Notes:', margin, y)
    y += 5
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(71, 85, 105)
    doc.text(patientInfo.notes, margin, y, { maxWidth: pageWidth - 2 * margin })
    y += 12
  }

  // Footer Disclaimer
  doc.setFillColor(254, 243, 199) // amber-100
  doc.setDrawColor(245, 158, 11) // amber-500
  doc.roundedRect(margin, 260, pageWidth - 2 * margin, 24, 2, 2, 'FD')

  doc.setFontSize(7.5)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(180, 83, 9)
  doc.text('MANDATORY CLINICAL SAFETY DISCLAIMER:', margin + 4, 265)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(146, 64, 14)
  const disclaimer =
    'BoneVision is an AI-assisted screening decision-support tool, NOT a diagnostic medical device. ' +
    'Predictions are probabilistic estimations and must be independently verified by a licensed radiologist ' +
    'or qualified healthcare provider prior to any clinical diagnosis, treatment, or patient management decision.'
  doc.text(disclaimer, margin + 4, 270, { maxWidth: pageWidth - 2 * margin - 8 })

  // Save PDF
  const filename = `BoneVision_Report_${pName.replace(/\s+/g, '_')}_${Date.now()}.pdf`
  doc.save(filename)
}
