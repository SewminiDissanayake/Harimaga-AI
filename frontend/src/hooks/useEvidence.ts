/*
  useEvidence.ts
  --------------
  Holds the evidence files attached to the current request.
  Each request has a random `requestId`; the backend links files only to that
  ID (no name, no account) and deletes them after 24 hours.
*/
import { useCallback, useState } from 'react'
import { deleteEvidence, uploadEvidence, type Evidence } from '../lib/api'
import { MAX_FILES, sanitizeImage } from '../lib/sanitizeImage'

export function useEvidence(requestId: string) {
  const [items, setItems] = useState<Evidence[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string>()

  const add = useCallback(
    async (files: FileList | File[]) => {
      setError(undefined)
      setUploading(true)
      try {
        let count = items.length
        for (const original of Array.from(files)) {
          if (count >= MAX_FILES) {
            setError(`Maximum ${MAX_FILES} files per request.`)
            break
          }
          const { file, privacyProcessed } = await sanitizeImage(original)
          const evidence = await uploadEvidence(file, requestId, privacyProcessed)
          setItems((prev) => [...prev, evidence])
          count++
        }
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setUploading(false)
      }
    },
    [items.length, requestId],
  )

  const remove = useCallback(
    async (id: string) => {
      setItems((prev) => prev.filter((e) => e.id !== id))
      await deleteEvidence(id, requestId)
    },
    [requestId],
  )

  /** Delete everything (used when starting a new request). */
  const clearAll = useCallback(async () => {
    const old = items
    setItems([])
    setError(undefined)
    await Promise.all(old.map((e) => deleteEvidence(e.id, requestId)))
  }, [items, requestId])

  return { items, uploading, error, add, remove, clearAll }
}
