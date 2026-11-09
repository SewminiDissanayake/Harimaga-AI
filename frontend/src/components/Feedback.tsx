/*
  Feedback: "Was this helpful?" with yes / no.
  Only the category and the answer are sent; nothing about the person.
  The counts show which categories HariMaga gets wrong most often.
*/
import { AnimatePresence, motion } from 'motion/react'
import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { sendFeedback } from '../lib/api'
import type { Strings } from '../lib/i18n'

export function Feedback({ t, issueKey }: { t: Strings; issueKey: string }) {
  const [sent, setSent] = useState(false)

  const answer = (helpful: boolean) => {
    setSent(true)
    sendFeedback(issueKey, helpful)
  }

  return (
    <div className="flex min-h-11 flex-wrap items-center gap-3 px-1 text-sm text-muted">
      <AnimatePresence mode="wait">
        {sent ? (
          <motion.p key="thanks" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} role="status">
            {t.feedbackThanks}
          </motion.p>
        ) : (
          <motion.div key="ask" exit={{ opacity: 0 }} className="flex items-center gap-3">
            <span>{t.feedbackQ}</span>
            {[
              { helpful: true, Icon: ThumbsUp, label: t.feedbackYes },
              { helpful: false, Icon: ThumbsDown, label: t.feedbackNo },
            ].map(({ helpful, Icon, label }) => (
              <motion.button
                key={label}
                type="button"
                whileTap={{ scale: 0.85, rotate: helpful ? -12 : 12 }}
                onClick={() => answer(helpful)}
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-white px-3 py-1.5 font-medium text-ink hover:border-forest"
              >
                <Icon className="size-4" aria-hidden />
                {label}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
