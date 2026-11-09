/*
  Hero: first thing people see. Big Sinhala promise + the 3D island.
  The coast illustration sits at the bottom as a landscape layer.
*/
import { motion, useReducedMotion } from 'motion/react'
import { BadgeCheck, Lock, MapPin } from 'lucide-react'
import type { Lang, Strings } from '../lib/i18n'
import { IslandStage } from './IslandStage'

export function Hero({ t, lang }: { t: Strings; lang: Lang }) {
  const reduce = useReducedMotion()
  const lines = t.tagline.split(/(?<=\.)\s+/)

  return (
    <section className="relative isolate overflow-hidden rounded-[28px] bg-[linear-gradient(135deg,#0b3a2c_0%,#11523f_45%,#0d6b6b_100%)] text-white shadow-[0_30px_60px_-30px_rgb(11_58_44/0.8)]">
      {/* Landscape layer */}
      <img
        src="/art/sri-lanka-coast-v8.svg"
        alt=""
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 w-full opacity-45 mix-blend-soft-light"
      />
      {/* Soft light from the top-right */}
      <div aria-hidden className="absolute -top-32 -right-24 -z-10 size-96 rounded-full bg-saffron/25 blur-3xl" />

      <div className="grid items-center gap-2 px-6 pt-5 pb-7 sm:px-10 sm:py-10 md:grid-cols-[1.5fr_1fr]">
        <div className="order-2 md:order-1">
          <h1 className={`font-display leading-[1.05] font-extrabold tracking-tight ${
            // Tamil words are longer, so the headline is a little smaller
            lang === 'ta' ? 'text-[1.7rem] sm:text-4xl lg:text-5xl' : 'text-[2.3rem] sm:text-5xl lg:text-6xl'
          }`}>
            {lines.map((line, i) => (
              <motion.span
                key={line}
                className={`block ${i === 1 ? 'text-saffron' : ''}`}
                initial={reduce ? false : { opacity: 0, y: 24, rotateX: -50 }}
                animate={{ opacity: 1, y: 0, rotateX: 0 }}
                transition={{ delay: 0.15 + i * 0.15, duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
                style={{ transformOrigin: 'bottom', perspective: 600 }}
              >
                {line}
              </motion.span>
            ))}
          </h1>
          <p className="mt-4 max-w-[34rem] text-[15px] leading-7 text-white/80 sm:text-base">{t.intro}</p>

          <ul className="mt-6 hidden flex-wrap gap-2 text-[13px] sm:flex">
            {[
              [BadgeCheck, t.trust1],
              [MapPin, t.trust2],
              [Lock, t.trust3],
            ].map(([Icon, text]) => {
              const I = Icon as typeof BadgeCheck
              return (
                <li
                  key={text as string}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 backdrop-blur"
                >
                  <I className="size-4 text-saffron" aria-hidden />
                  {text as string}
                </li>
              )
            })}
          </ul>
        </div>

        <div className="order-1 flex justify-center md:order-2">
          <div className="hidden sm:block">
            <IslandStage size={300} />
          </div>
          <div className="sm:hidden">
            <IslandStage size={140} />
          </div>
        </div>
      </div>
    </section>
  )
}
