/*
  DraftDialog: the complaint draft in a pop-up the user can edit.
  Uses the built-in HTML <dialog> element, which handles focus and the
  Escape key for us (good for keyboard and screen-reader users).
*/
import { motion } from 'motion/react'
import { Check, Copy, Mail, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { Strings } from '../lib/i18n'

interface Props {
  t: Strings
  draft: { subject: string; body: string; review_note: string }
  authorityEmail?: string
  onClose: () => void
}

export function DraftDialog({ t, draft, authorityEmail, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const [subject, setSubject] = useState(draft.subject)
  const [body, setBody] = useState(draft.body)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    ref.current?.showModal()
  }, [])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`${subject}\n\n${body}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard blocked: the user can still select the text */
    }
  }

  const mailto = authorityEmail
    ? `mailto:${authorityEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
    : undefined

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-labelledby="draft-title"
      className="m-auto w-[min(42rem,calc(100%-2rem))] overflow-visible bg-transparent p-0 backdrop:bg-ink/50 backdrop:backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, rotateX: -20, y: 30 }}
        animate={{ opacity: 1, rotateX: 0, y: 0 }}
        transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
        style={{ transformPerspective: 900 }}
        className="rounded-3xl bg-white p-5 shadow-2xl sm:p-6"
      >
        <div className="flex items-start gap-3">
          <h2 id="draft-title" className="mr-auto font-display text-2xl font-extrabold text-forest-dark">
            {t.draftTitle}
          </h2>
          <button
            type="button"
            onClick={() => ref.current?.close()}
            aria-label={t.close}
            className="grid size-9 place-items-center rounded-full hover:bg-leaf"
          >
            <X className="size-5" aria-hidden />
          </button>
        </div>

        <p className="mt-1 rounded-xl bg-saffron/15 px-3 py-2 text-sm text-ink/80">{t.draftReview}</p>

        <label className="mt-4 block text-sm font-semibold text-forest" htmlFor="draft-subject">
          {t.subject}
        </label>
        <input
          id="draft-subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className="mt-1 w-full rounded-xl border border-line px-3 py-2.5 text-[15px] outline-none focus:border-forest"
        />

        <label className="mt-3 block text-sm font-semibold text-forest" htmlFor="draft-body">
          {t.body}
        </label>
        <textarea
          id="draft-body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={12}
          className="mt-1 w-full resize-y rounded-xl border border-line px-3 py-2.5 text-[14px] leading-6 outline-none focus:border-forest"
        />

        <div className="mt-4 flex flex-wrap justify-end gap-2">
          {mailto && (
            <a
              href={mailto}
              className="inline-flex items-center gap-2 rounded-full border border-forest/40 px-4 py-2.5 text-sm font-semibold text-forest hover:bg-leaf"
            >
              <Mail className="size-4" aria-hidden />
              {t.emailDraft}
            </a>
          )}
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-2 rounded-full bg-forest px-4 py-2.5 text-sm font-semibold text-white hover:bg-forest-dark"
          >
            {copied ? <Check className="size-4" aria-hidden /> : <Copy className="size-4" aria-hidden />}
            {copied ? t.copied : t.copy}
          </button>
        </div>
      </motion.div>
    </dialog>
  )
}
