/*
  NextSteps: shown under the result card.
    1. Attach evidence (photos / PDF), privacy-cleaned in the browser
    2. Prepare a complaint draft the user can edit, copy or email
*/
import { motion } from 'motion/react'
import { FileText, ImagePlus, Loader2, PenLine, X } from 'lucide-react'
import { useRef, useState } from 'react'
import type { Evidence } from '../lib/api'
import type { Strings } from '../lib/i18n'
import { DraftDialog } from './DraftDialog'

interface Props {
  t: Strings
  evidence: Evidence[]
  uploading: boolean
  error?: string
  onAdd: (files: FileList) => void
  onRemove: (id: string) => void
  onPrepareDraft: () => Promise<{ subject: string; body: string; review_note: string }>
  authorityEmail?: string
}

export function NextSteps({ t, evidence, uploading, error, onAdd, onRemove, onPrepareDraft, authorityEmail }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState<{ subject: string; body: string; review_note: string }>()
  const [preparing, setPreparing] = useState(false)
  const [draftError, setDraftError] = useState<string>()

  const prepare = async () => {
    setPreparing(true)
    setDraftError(undefined)
    try {
      setDraft(await onPrepareDraft())
    } catch (err) {
      setDraftError((err as Error).message)
    } finally {
      setPreparing(false)
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="rounded-3xl border border-line bg-white p-5"
    >
      <h3 className="font-display text-xl font-extrabold text-forest-dark">{t.nextTitle}</h3>

      {/* Evidence */}
      <div className="mt-3">
        <p className="text-sm text-muted">{t.evidenceHelp}</p>

        {evidence.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-2.5">
            {evidence.map((e) => (
              <motion.li
                key={e.id}
                initial={{ scale: 0.6, opacity: 0, rotate: -6 }}
                animate={{ scale: 1, opacity: 1, rotate: 0 }}
                className="relative size-20 overflow-hidden rounded-xl border border-line bg-leaf/50"
              >
                {e.mime_type.startsWith('image/') ? (
                  <img src={e.preview_url} alt={e.filename} className="size-full object-cover" />
                ) : (
                  <a href={e.preview_url} target="_blank" rel="noopener noreferrer" className="grid size-full place-items-center text-forest">
                    <FileText className="size-8" aria-hidden />
                    <span className="sr-only">{e.filename}</span>
                  </a>
                )}
                <button
                  type="button"
                  onClick={() => onRemove(e.id)}
                  aria-label={t.removeEvidence}
                  className="absolute top-1 right-1 grid size-6 place-items-center rounded-full bg-ink/70 text-white hover:bg-maroon"
                >
                  <X className="size-3.5" aria-hidden />
                </button>
              </motion.li>
            ))}
          </ul>
        )}

        {error && <p className="mt-2 text-sm text-maroon">{error}</p>}
        {evidence.length > 0 && <p className="mt-2 text-xs text-muted">{t.evidenceAutoDelete}</p>}
      </div>

      {/* Actions */}
      <div className="mt-4 flex flex-wrap gap-2">
        <input
          ref={fileRef}
          type="file"
          multiple
          hidden
          accept=".jpg,.jpeg,.jfif,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
          onChange={(e) => {
            if (e.target.files?.length) onAdd(e.target.files)
            e.target.value = '' // allow choosing the same file again
          }}
        />
        <button
          type="button"
          disabled={uploading}
          onClick={() => fileRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-full border border-forest/40 px-4 py-2.5 text-sm font-semibold text-forest hover:bg-leaf disabled:opacity-60"
        >
          {uploading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <ImagePlus className="size-4" aria-hidden />}
          {uploading ? t.uploading : t.addEvidence}
        </button>
        <button
          type="button"
          disabled={preparing || uploading}
          onClick={prepare}
          className="inline-flex items-center gap-2 rounded-full bg-saffron px-4 py-2.5 text-sm font-semibold text-forest-dark shadow-[0_8px_20px_-10px_rgb(227_167_47/0.9)] hover:brightness-105 disabled:opacity-60"
        >
          {preparing ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <PenLine className="size-4" aria-hidden />}
          {t.draftButton}
        </button>
      </div>
      {draftError && <p className="mt-2 text-sm text-maroon">{draftError}</p>}

      {draft && (
        <DraftDialog t={t} draft={draft} authorityEmail={authorityEmail} onClose={() => setDraft(undefined)} />
      )}
    </motion.section>
  )
}
