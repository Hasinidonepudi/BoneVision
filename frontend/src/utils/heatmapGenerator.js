/**
 * Client-Side Grad-CAM Heatmap Generator
 * Creates an anatomical attention heatmap (Jet colormap) focused on the knee joint
 * (medial/lateral tibial plateau and femoral condyles) when backend is in demo/client mode.
 */

function jetColormap(val) {
  // val: 0.0 to 1.0
  // Jet colormap: Blue -> Cyan -> Yellow -> Orange -> Red
  const fourVal = 4 * val
  const r = Math.min(Math.max(1.5 - Math.abs(fourVal - 3), 0), 1)
  const g = Math.min(Math.max(1.5 - Math.abs(fourVal - 2), 0), 1)
  const b = Math.min(Math.max(1.5 - Math.abs(fourVal - 1), 0), 1)
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)]
}

export async function generateClientGradCam(file) {
  return new Promise((resolve) => {
    if (!file) {
      resolve(null)
      return
    }

    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        const width = 300
        const height = 300
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')

        // First, draw original image into canvas to extract bone luminance mask
        ctx.drawImage(img, 0, 0, width, height)
        const origData = ctx.getImageData(0, 0, width, height).data

        // Knee joint center typically at (48%, 52%)
        const centerX = width * 0.48
        const centerY = height * 0.52

        // Create output imageData
        const imgData = ctx.createImageData(width, height)
        const data = imgData.data

        const sigmaX = width * 0.22
        const sigmaY = height * 0.14

        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            const dx = x - centerX
            const dy = y - centerY

            // Dual lobe for medial and lateral tibial joint spaces
            const dMedial = Math.hypot(dx + width * 0.08, dy)
            const dLateral = Math.hypot(dx - width * 0.08, dy * 1.1)

            const gMedial = Math.exp(-(dMedial * dMedial) / (2 * sigmaX * sigmaY))
            const gLateral = Math.exp(-(dLateral * dLateral) / (2 * sigmaX * sigmaY)) * 0.85

            let intensity = Math.max(gMedial, gLateral)

            // Rectification #3: Bone anatomical boundary guidance
            // Modulate heatmap by underlying bone opacity (prevents bleed into air/background)
            const origIdx = (y * width + x) * 4
            const boneLuminance = (origData[origIdx] * 0.299 + origData[origIdx + 1] * 0.587 + origData[origIdx + 2] * 0.114) / 255.0
            const boneMask = Math.min(Math.max((boneLuminance - 0.12) / 0.5, 0), 1.0)
            intensity = intensity * (0.35 + 0.65 * boneMask)

            // Normalize and threshold
            intensity = Math.min(Math.max(intensity, 0), 1)

            const idx = (y * width + x) * 4

            if (intensity > 0.08) {
              const [r, g, b] = jetColormap(intensity)
              data[idx] = r
              data[idx + 1] = g
              data[idx + 2] = b
              data[idx + 3] = Math.round(intensity * 255) // alpha proportional to intensity
            } else {
              data[idx] = 0
              data[idx + 1] = 0
              data[idx + 2] = 0
              data[idx + 3] = 0
            }
          }
        }

        ctx.putImageData(imgData, 0, 0)
        const base64Png = canvas.toDataURL('image/png').split(',')[1]
        URL.revokeObjectURL(url)
        resolve(base64Png)
      } catch (err) {
        console.warn('[BoneVision] Client heatmap generation error:', err)
        URL.revokeObjectURL(url)
        resolve(null)
      }
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(null)
    }

    img.src = url
  })
}
