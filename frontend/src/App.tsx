/*
  App.tsx: the page layout.

  Before the user types:   Hero (3D island) + CategoryGrid
  During the conversation: chat column + SidePanel (wide screens)
  Always:                  Header on top, Composer fixed at the bottom
*/
import { AnimatePresence, motion } from 'motion/react'
import { RotateCcw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { CategoryGrid } from './components/CategoryGrid'
import { ChatMessage } from './components/ChatMessage'
import { Composer } from './components/Composer'
import { Feedback } from './components/Feedback'
import { Hero } from './components/Hero'
import { NextSteps } from './components/NextSteps'
import { SidePanel } from './components/SidePanel'
import { useEvidence } from './hooks/useEvidence'
import { useHariMaga } from './hooks/useHariMaga'
import { checkHealth, newRequestId, prepareDraft } from './lib/api'
import { categoryByKey } from './lib/categories'
import { STRINGS, type Lang } from './lib/i18n'

function loadLang(): Lang {
  try {
    const saved = localStorage.getItem('harimaga_lang')
    return saved === 'en' || saved === 'ta' ? saved : 'si'
  } catch {
    return 'si'
  }
}

export default function App() {
  const [lang, setLang] = useState<Lang>(loadLang)
  const [backendOk, setBackendOk] = useState(true)
  const [prefill, setPrefill] = useState<{ text: string; n: number }>()
  const [category, setCategory] = useState<string>()
  const { messages, loading, phase, allowSkip, detected, problem, answers, submit, reset } = useHariMaga(category)
  // A new random ID for each request; evidence files are linked only to it
  const [requestId, setRequestId] = useState(newRequestId)
  const evidence = useEvidence(requestId)
  const t = STRINGS[lang]
  const bottomRef = useRef<HTMLDivElement>(null)
  const chatting = messages.length > 0
  const selectedCat = categoryByKey(category)

  useEffect(() => {
    checkHealth().then(setBackendOk)
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    try {
      localStorage.setItem('harimaga_lang', lang)
    } catch {
      /* private mode: ignore */
    }
  }, [lang])

  // Keep the newest message in view. For a result card, show its TOP.
  useEffect(() => {
    const last = messages[messages.length - 1]
    if (last?.role === 'assistant' && last.kind === 'route') {
      document.getElementById(`msg-${last.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else if (messages.length) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages, loading])

  const firstUserText = messages.find((m) => m.role === 'user')?.text
  const placeholder =
    phase === 'asking' ? (allowSkip ? t.placeholderSkip : t.placeholderAnswer)
    : phase === 'done' ? t.placeholderDone
    : t.placeholderNew

  const startOver = () => {
    evidence.clearAll()
    setRequestId(newRequestId())
    reset()
    setCategory(undefined)
  }

  const handleSend = (text: string) => {
    // After a finished route, a new message is a new problem
    if (phase === 'done') {
      evidence.clearAll()
      setRequestId(newRequestId())
      setCategory(undefined)
    }
    submit(text)
  }

  // The last message, if it is a result card
  const last = messages[messages.length - 1]
  const lastRoute = last?.role === 'assistant' && last.kind === 'route' ? last.route : undefined
  const authorityEmail = lastRoute?.contacts.find((c) => c.kind === 'email')?.value

  return (
    <div className="flex h-full flex-col bg-[radial-gradient(60rem_30rem_at_100%_-10%,#cfe8dd_0%,transparent_60%),radial-gradient(40rem_30rem_at_-10%_110%,#d7ecf0_0%,transparent_60%)]">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-white/60 bg-mist/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4">
          <motion.img
            src="/island.svg"
            alt=""
            className="size-10"
            whileHover={{ rotateY: 180 }}
            transition={{ duration: 0.6 }}
          />
          <div className="mr-auto leading-tight">
            <p className="font-display text-xl font-extrabold text-forest-dark">හරිමග</p>
            <p className="text-xs text-muted">HariMaga AI</p>
          </div>

          <div className="flex rounded-full border border-line bg-white p-0.5 text-sm" role="group" aria-label="Language">
            {(['si', 'ta', 'en'] as const).map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => setLang(l)}
                aria-pressed={lang === l}
                className={`rounded-full px-2.5 py-1 font-medium sm:px-3 ${lang === l ? 'bg-forest text-white' : 'text-muted hover:text-ink'}`}
              >
                {{ si: 'සිං', ta: 'த', en: 'EN' }[l]}
              </button>
            ))}
          </div>

          {chatting && (
            <button
              type="button"
              onClick={startOver}
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium text-forest hover:bg-leaf"
            >
              <RotateCcw className="size-4" aria-hidden />
              <span className="hidden sm:inline">{t.newRequest}</span>
              <span className="sr-only sm:hidden">{t.newRequest}</span>
            </button>
          )}
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-4 pt-5 pb-8">
          {!backendOk && (
            <p className="mb-4 rounded-xl border border-maroon/25 bg-maroon/5 px-4 py-3 text-sm text-maroon">
              {t.backendDown}
            </p>
          )}

          <AnimatePresence mode="wait">
            {!chatting ? (
              <motion.div
                key="home"
                exit={{ opacity: 0, y: -20, transition: { duration: 0.25 } }}
              >
                <Hero t={t} lang={lang} />
                <CategoryGrid t={t} lang={lang} selected={category} onSelect={setCategory} />
              </motion.div>
            ) : (
              <motion.div
                key="chat"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"
              >
                <div className="mx-auto w-full max-w-3xl space-y-4" aria-live="polite">
                  {messages.map((m, i) => (
                    <div key={m.id} id={`msg-${m.id}`} className="scroll-mt-20">
                      <ChatMessage
                        m={m}
                        isLatest={i === messages.length - 1}
                        disabled={loading}
                        problem={firstUserText}
                        t={t}
                        lang={lang}
                        onOption={(o) => submit(o.value, o.label)}
                      />
                    </div>
                  ))}
                  {lastRoute && !loading && (
                    <NextSteps
                      t={t}
                      evidence={evidence.items}
                      uploading={evidence.uploading}
                      error={evidence.error}
                      onAdd={evidence.add}
                      onRemove={evidence.remove}
                      authorityEmail={authorityEmail}
                      onPrepareDraft={() =>
                        prepareDraft({
                          text: problem,
                          answers,
                          evidenceIds: evidence.items.map((e) => e.id),
                          requestId,
                          categoryHint: category,
                        })
                      }
                    />
                  )}
                  {lastRoute && !loading && <Feedback key={last!.id} t={t} issueKey={lastRoute.issueKey} />}
                  {loading && <TypingDots label={t.thinking} />}
                  <div ref={bottomRef} />
                </div>
                <SidePanel t={t} lang={lang} phase={phase} categoryKey={category ?? detected} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Composer */}
      <footer className="border-t border-white/60 bg-mist/80 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl">
        <div className="mx-auto max-w-3xl px-4 pt-3 pb-3">
          <AnimatePresence>
            {selectedCat && !chatting && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                className="mb-2 flex flex-wrap items-center gap-2 text-sm"
              >
                <span className="inline-flex items-center gap-1.5 rounded-full bg-forest py-1 pr-1 pl-3 text-white">
                  <selectedCat.icon className="size-4" aria-hidden />
                  {t.selected}: {selectedCat[lang]}
                  <button
                    type="button"
                    onClick={() => setCategory(undefined)}
                    aria-label={t.clearCategory}
                    className="grid size-6 place-items-center rounded-full hover:bg-white/20"
                  >
                    <X className="size-3.5" aria-hidden />
                  </button>
                </span>
                <button
                  type="button"
                  onClick={() => setPrefill({ text: selectedCat.example, n: Date.now() })}
                  className="truncate rounded-full border border-line bg-white px-3 py-1 text-muted hover:border-forest/50 hover:text-ink"
                >
                  {t.tryExample}: “{selectedCat.example}”
                </button>
              </motion.div>
            )}
          </AnimatePresence>
          <Composer
            placeholder={placeholder}
            sendLabel={t.send}
            disabled={loading}
            onSend={handleSend}
            prefill={prefill}
          />
          <p className="mt-2 text-center text-xs text-muted">
            {t.privacy} {t.verified}
          </p>
        </div>
      </footer>
    </div>
  )
}

function TypingDots({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted" role="status">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="size-2 rounded-full bg-forest/60"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
      </span>
      {label}
    </div>
  )
}
