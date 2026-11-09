/*
  RouteCard: shows where the citizen should take their problem.
  Drawn as a "route": a saffron path from the problem to the authority.
*/
import { ExternalLink, Mail, MessageCircle, Phone, ShieldAlert } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import type { Contact, RouteView } from '../lib/normalize'
import { labelFor } from '../lib/normalize'
import { translateNote, translateOption } from '../lib/backendText'
import { DISTRICTS, districtLabel } from '../lib/districts'
import type { Lang, Strings } from '../lib/i18n'

interface Props {
  route: RouteView
  problem?: string
  t: Strings
  lang: Lang
}

export function RouteCard({ route, problem, t, lang }: Props) {
  // Group contacts: ones without a group first, then by local authority / station
  const groups = new Map<string, Contact[]>()
  for (const c of route.contacts) {
    const key = c.group ?? ''
    groups.set(key, [...(groups.get(key) ?? []), c])
  }

  const reduce = useReducedMotion()
  // Show the district in the chosen language (backend sends the English name)
  const d = DISTRICTS.find((x) => x.value.toLowerCase() === route.district?.toLowerCase())
  const district = d ? districtLabel(d, lang) : route.district
  const notes = route.notes.map((n) => translateNote(n, lang)).filter((n): n is string => Boolean(n))

  return (
    // 3D entrance: the card swings up from a tilted position
    <motion.article
      initial={reduce ? false : { opacity: 0, rotateX: 28, y: 30 }}
      animate={{ opacity: 1, rotateX: 0, y: 0 }}
      transition={{ duration: 0.65, ease: [0.2, 0.8, 0.2, 1] }}
      style={{ transformPerspective: 1000, transformOrigin: 'top' }}
      className="w-full overflow-hidden rounded-3xl border border-line bg-white shadow-[0_24px_50px_-30px_rgb(19_36_30/0.5)]"
    >
      {route.emergency && (
        <div className="flex gap-3 bg-maroon px-5 py-4 text-white" role="alert">
          <ShieldAlert className="mt-0.5 size-5 shrink-0" aria-hidden />
          <div>
            <a href="tel:119" className="text-lg font-bold underline-offset-4 hover:underline">
              {t.emergencyTitle}
            </a>
            <p className="mt-0.5 text-sm text-white/85">{t.emergencyBody}</p>
          </div>
        </div>
      )}

      {/* The route: problem -> authority */}
      <div className="relative px-5 pt-5 pb-4">
        {problem && (
          <div className="relative flex gap-3 pb-5">
            {/* The route line "draws" itself from the problem dot down to the authority dot */}
            <motion.span
              aria-hidden
              initial={reduce ? false : { scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ delay: 0.35, duration: 0.7, ease: 'easeInOut' }}
              style={{ transformOrigin: 'top' }}
              className="absolute top-[22px] -bottom-[6px] left-[4.5px] w-[3px] rounded-full bg-[repeating-linear-gradient(to_bottom,var(--color-saffron)_0_8px,transparent_8px_13px)]"
            />
            <span aria-hidden className="mt-1.5 size-3 shrink-0 rounded-full border-2 border-saffron bg-white" />
            <div className="min-w-0">
              <p className="text-xs text-muted">{t.yourProblem}</p>
              <p className="truncate text-sm text-ink/80">{problem}</p>
            </div>
          </div>
        )}
        <div className="relative flex gap-3">
          <motion.span
            aria-hidden
            initial={reduce ? false : { scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 1, type: 'spring', stiffness: 400, damping: 12 }}
            className="mt-2 size-3 shrink-0 rounded-full bg-forest ring-4 ring-leaf"
          />
          <div className="min-w-0">
            <p className="text-xs text-muted">{t.authority}</p>
            <h3 className="font-display text-2xl leading-tight font-extrabold text-forest-dark">
              {route.authority}
            </h3>
            {(route.subtitle || district) && (
              <p className="mt-1 text-sm text-muted">
                {[route.subtitle && translateOption(route.subtitle, lang), district && `${t.area}: ${district}`]
                  .filter(Boolean)
                  .join(', ')}
              </p>
            )}
          </div>
        </div>
      </div>

      {route.contacts.length > 0 && (
        <Section title={t.contacts}>
          {[...groups.entries()].map(([group, contacts]) => (
            <div key={group || 'main'} className="not-first:mt-3">
              {group && <p className="mb-1.5 text-sm font-semibold text-ink">{group}</p>}
              <ul className="divide-y divide-line rounded-xl border border-line">
                {contacts.map((c) => (
                  <ContactRow key={`${c.kind}-${c.value}`} c={c} t={t} />
                ))}
              </ul>
            </div>
          ))}
        </Section>
      )}

      {route.steps.length > 0 && (
        <Section title={t.steps}>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm leading-relaxed marker:text-forest">
            {route.steps.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ol>
        </Section>
      )}

      {route.required.length > 0 && (
        <Section title={t.prepare}>
          <ul className="flex flex-wrap gap-1.5">
            {route.required.map((k) => (
              <li key={k} className="rounded-full bg-leaf px-3 py-1 text-[13px] text-forest-dark">
                {labelFor(k, lang)}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {notes.length > 0 && (
        <Section title={t.notes}>
          <ul className="space-y-1.5 text-sm leading-relaxed text-ink/85">
            {notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </Section>
      )}
    </motion.article>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line px-5 py-4">
      <h4 className="mb-2.5 text-sm font-semibold text-forest">{title}</h4>
      {children}
    </section>
  )
}

function ContactRow({ c, t }: { c: Contact; t: Strings }) {
  const action = {
    phone: { icon: Phone, text: t.call },
    whatsapp: { icon: MessageCircle, text: t.whatsapp },
    email: { icon: Mail, text: t.email },
    url: { icon: ExternalLink, text: t.open },
    text: null,
  }[c.kind]

  const isUrl = c.kind === 'url'
  return (
    <li className="flex items-center gap-3 px-3.5 py-2.5">
      <div className="min-w-0 flex-1">
        <p className="text-[13px] text-muted">{c.label}</p>
        <p className={`text-sm font-medium text-ink ${isUrl ? 'truncate' : 'break-words'}`}>
          {isUrl ? new URL(c.value).hostname.replace(/^www\./, '') : c.value}
        </p>
      </div>
      {action && c.href && (
        <a
          href={c.href}
          target={c.kind === 'url' || c.kind === 'whatsapp' ? '_blank' : undefined}
          rel="noopener noreferrer"
          className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-forest px-3.5 py-2 text-[13px] font-semibold text-white hover:bg-forest-dark"
        >
          <action.icon className="size-4" aria-hidden />
          {action.text}
        </a>
      )}
    </li>
  )
}
