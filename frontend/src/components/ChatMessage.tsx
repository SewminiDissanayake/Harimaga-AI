/*
  ChatMessage: one bubble in the conversation.
  User messages sit on the right; HariMaga's on the left.

  Questions from the backend are translated with backendText.ts.
  When the backend asks for a district but sends no options,
  we show the 25 districts as buttons, so nobody has to type or spell them.
*/
import { AlertCircle } from 'lucide-react'
import type { Message, NormalOption } from '../hooks/useHariMaga'
import { translateOption, translateQuestion } from '../lib/backendText'
import { DISTRICT_FIELDS, DISTRICTS, districtLabel } from '../lib/districts'
import type { Lang, Strings } from '../lib/i18n'
import { RouteCard } from './RouteCard'

interface Props {
  m: Message
  isLatest: boolean
  disabled: boolean
  problem?: string
  t: Strings
  lang: Lang
  onOption: (o: NormalOption) => void
}

const chip =
  'rounded-full border border-forest/40 bg-white px-4 py-2 text-sm font-medium text-forest transition-colors hover:border-forest hover:bg-leaf disabled:opacity-50'

export function ChatMessage({ m, isLatest, disabled, problem, t, lang, onOption }: Props) {
  if (m.role === 'user') {
    return (
      <div className="animate-rise flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-forest px-4 py-2.5 text-[15px] leading-6 whitespace-pre-wrap text-white">
          {m.text}
        </p>
      </div>
    )
  }

  if (m.kind === 'route') {
    return (
      <div className="animate-rise space-y-2">
        <p className="text-[15px] text-ink">{t.routeFound}</p>
        <RouteCard route={m.route} problem={problem} t={t} lang={lang} />
      </div>
    )
  }

  if (m.kind === 'error') {
    return (
      <div className="animate-rise flex gap-2.5 rounded-2xl border border-maroon/25 bg-maroon/5 px-4 py-3 text-[15px] text-maroon">
        <AlertCircle className="mt-0.5 size-5 shrink-0" aria-hidden />
        <p>{m.code === 'rate_limited' ? t.tooMany : m.text}</p>
      </div>
    )
  }

  // Clarification question
  const askDistrict = m.options.length === 0 && m.field && DISTRICT_FIELDS.has(m.field)

  return (
    <div className="animate-rise max-w-[92%] space-y-2.5">
      {m.hint && <p className="text-sm font-medium text-maroon">{translateQuestion(m.hint, lang)}</p>}
      <p className="rounded-2xl rounded-bl-md border border-line bg-white px-4 py-3 text-[15px] leading-6">
        {translateQuestion(m.text, lang)}
      </p>

      {/* Options are only clickable on the latest question */}
      {isLatest && m.options.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {m.options.map((o) => (
            <button
              key={String(o.value)}
              type="button"
              disabled={disabled}
              // The backend gets the original value; the chat shows the translated label
              onClick={() => onOption({ value: o.value, label: translateOption(o.label, lang) })}
              className={chip}
            >
              {translateOption(o.label, lang)}
            </button>
          ))}
        </div>
      )}

      {isLatest && askDistrict && (
        <div role="group" aria-label={t.chooseDistrict}>
          <p className="mb-2 text-sm text-muted">{t.chooseDistrict}</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {DISTRICTS.map((d) => (
              <button
                key={d.value}
                type="button"
                disabled={disabled}
                onClick={() => onOption({ value: d.value, label: districtLabel(d, lang) })}
                className="rounded-xl border border-line bg-white px-3 py-2 text-left text-sm font-medium text-ink transition-colors hover:border-forest hover:bg-leaf disabled:opacity-50"
              >
                {districtLabel(d, lang)}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
