/*
  sanitizeImage.ts
  ----------------
  Photos from phones contain hidden "EXIF" data: GPS location, phone model,
  date and time. Before uploading, we redraw the photo on a <canvas> and save
  it again. A canvas only keeps the pixels, so all hidden data is removed.
  (Ported from the old harimaga-ui-v8.js sanitizeImageFile.)
*/

export const MAX_FILES = 6
export const MAX_BYTES = 10 * 1024 * 1024

export async function sanitizeImage(file: File): Promise<{ file: File; privacyProcessed: boolean }> {
  const name = file.name.toLowerCase()

  if (name.endsWith('.heic') || name.endsWith('.heif')) {
    throw new Error('HEIC photo: please save it as JPG first, then attach it again.')
  }
  if (file.size > MAX_BYTES) {
    throw new Error('This file is larger than 10 MB.')
  }
  // PDFs are uploaded as they are
  if (!file.type.startsWith('image/')) {
    return { file, privacyProcessed: false }
  }

  let bitmap: ImageBitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    throw new Error('This photo could not be opened. Please use JPG, PNG, WEBP or PDF.')
  }

  // Also shrink very large photos (faster upload on mobile data)
  const maxSide = 1800
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height))
  const width = Math.max(1, Math.round(bitmap.width * scale))
  const height = Math.max(1, Math.round(bitmap.height * scale))

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  canvas.getContext('2d')!.drawImage(bitmap, 0, 0, width, height)
  bitmap.close()

  const type = ['image/jpeg', 'image/png', 'image/webp'].includes(file.type) ? file.type : 'image/jpeg'
  const ext = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp' }[type]!

  const blob = await new Promise<Blob>((resolve, reject) =>
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error('Could not prepare the photo.'))),
      type,
      type === 'image/png' ? undefined : 0.9,
    ),
  )

  // The extension must match the new type, because the backend checks it
  return { file: new File([blob], `evidence${ext}`, { type }), privacyProcessed: true }
}
