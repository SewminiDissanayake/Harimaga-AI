/*
  SidePanel: shown on wide screens next to the chat.
  Shows progress (a real sequence: understand -> clarify -> route)
  and an illustration for the current category.
*/
import { motion } from 'motion/react'
import { Check } from 'lucide-react'
import type { Phase } from '../hooks/useHariMaga'
import { categoryByKey, categorySub } from '../lib/categories'
import type { Lang, Strings } from '../lib/i18n'

interface Props {
  t: Strings
  lang: Lang
  phase: Phase
  categoryKey?: string
}

export function SidePanel({ t, lang, phase, categoryKey }: Props) {
  const current = phase === 'idle' ? 0 : phase === 'asking' ? 1 : 3
  const steps = [t.stepUnderstand, t.stepClarify, t.stepRoute]
  const cat = categoryByKey(categoryKey)

  return (
    <aside className="sticky top-24 hidden space-y-4 self-start lg:block">
      <div className="overflow-hidden rounded-3xl bg-[linear-gradient(160deg,#0b3a2c,#11523f_60%,#0d6b6b)] p-5 text-white">
        <div className="flex items-center gap-3">
          <img src="/island.svg" alt="" className="size-12" />
          <h2 className="font-display text-2xl font-extrabold">{t.progressTitle}</h2>
        </div>
        <ol className="mt-5 space-y-3">
          {steps.map((s, i) => {
            const done = i < current
            const active = i === current || (current === 3 && i === 2)
            return (
              <li key={s} className="flex items-center gap-3">
                <motion.span
                  layout
                  className={`grid size-8 shrink-0 place-items-center rounded-full text-sm font-bold ${
                    done || current === 3
                      ? 'bg-saffron text-forest-dark'
                      : active
                        ? 'bg-white text-forest-dark'
                        : 'bg-white/10 text-white/60'
                  }`}
                >
                  {done || current === 3 ? <Check className="size-4" aria-hidden /> : i + 1}
                </motion.span>
                <span className={`text-sm ${active || done ? 'text-white' : 'text-white/55'}`}>{s}</span>
              </li>
            )
          })}
        </ol>
      </div>

      {cat && (
        <motion.div
          key={cat.key}
          initial={{ opacity: 0, rotateY: -25 }}
          animate={{ opacity: 1, rotateY: 0 }}
          transition={{ duration: 0.5 }}
          style={{ transformPerspective: 800 }}
          className="overflow-hidden rounded-3xl border border-line bg-white"
        >
          {cat.art ? (
            <img src={cat.art} alt="" className="h-36 w-full bg-leaf/40 object-cover" />
          ) : (
            <div className={`grid h-28 place-items-center bg-gradient-to-br ${cat.tone}`}>
              <cat.icon className="size-12" aria-hidden />
            </div>
          )}
          <div className="p-4">
            <p className="font-semibold text-ink">{cat[lang]}</p>
            <p className="text-sm text-muted">{categorySub(cat, lang)}</p>
          </div>
        </motion.div>
      )}
    </aside>
  )
}
