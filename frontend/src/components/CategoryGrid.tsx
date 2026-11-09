/*
  CategoryGrid: the 12 service categories as 3D tilt tiles.
  Tapping one selects it (tap again to unselect). The choice is sent to the
  backend as a hint; see classify_with_hint() in app.py.
*/
import { motion, useReducedMotion } from 'motion/react'
import { Check } from 'lucide-react'
import { CATEGORIES, categorySub } from '../lib/categories'
import type { Lang, Strings } from '../lib/i18n'
import { TiltCard } from './TiltCard'

interface Props {
  t: Strings
  lang: Lang
  selected?: string
  onSelect: (key: string | undefined) => void
}

export function CategoryGrid({ t, lang, selected, onSelect }: Props) {
  const reduce = useReducedMotion()

  return (
    <section className="mt-8">
      <h2 className="font-display text-2xl font-extrabold text-forest-dark sm:text-3xl">{t.categoriesTitle}</h2>
      <p className="mt-1 text-sm text-muted">{t.categoriesSub}</p>

      <ul className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-3 sm:gap-3 lg:grid-cols-4">
        {CATEGORIES.map((c, i) => {
          const isSel = selected === c.key
          const Icon = c.icon
          return (
            <motion.li
              key={c.key}
              initial={reduce ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 + i * 0.035, duration: 0.4 }}
            >
              <TiltCard
                selected={isSel}
                label={`${c[lang]}: ${categorySub(c, lang)}`}
                onClick={() => onSelect(isSel ? undefined : c.key)}
              >
                <span
                  className={`grid size-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br shadow-inner sm:size-12 ${c.tone}`}
                  style={{ transform: 'translateZ(25px)' }}
                >
                  <Icon className="size-5 sm:size-6" aria-hidden />
                </span>
                <span className="min-w-0" style={{ transform: 'translateZ(15px)' }}>
                  <span className="block text-[15px] leading-tight font-semibold text-ink">{c[lang]}</span>
                  <span className="mt-0.5 block truncate text-xs text-muted">
                    {categorySub(c, lang)}
                  </span>
                </span>
                {isSel && (
                  <span className="absolute top-2 right-2 grid size-5 place-items-center rounded-full bg-forest text-white">
                    <Check className="size-3.5" aria-hidden />
                  </span>
                )}
              </TiltCard>
            </motion.li>
          )
        })}
      </ul>
    </section>
  )
}
