/*
  useHariMaga.ts
  --------------
  A custom React hook that holds the whole conversation:
    - the original problem text
    - the answers collected so far
    - which field the backend is waiting for
    - the list of chat messages to show

  The flow is the same as the old app:
    1. user types a problem          -> POST /api/route {text, answers: {}}
    2. backend says needs_clarification -> show question + options
    3. user answers                  -> answers[needed_field] = value, POST again
    4. repeat until status is routed -> show the RouteCard
*/

import { useCallback, useState } from 'react'
import { routeProblem, type Option, type Routing } from '../lib/api'
import { normalizeRoute, type RouteView } from '../lib/normalize'

export type Message =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'assistant'; kind: 'question'; text: string; hint?: string; options: NormalOption[]; field?: string }
  | { id: number; role: 'assistant'; kind: 'route'; route: RouteView }
  | { id: number; role: 'assistant'; kind: 'error'; text: string; code?: string }

export interface NormalOption {
  value: unknown
  label: string
}

export type Phase = 'idle' | 'asking' | 'done'

/** Like Omit<Message, 'id'>, but works on each member of the union separately. */
type NewMessage = Message extends infer M ? (M extends Message ? Omit<M, 'id'> : never) : never

let nextId = 1

function normalizeOptions(options: Option[] | undefined): NormalOption[] {
  return (options ?? []).map((o) =>
    typeof o === 'object' && o !== null
      ? { value: o.value ?? o.label, label: String(o.label ?? o.value) }
      : { value: o, label: String(o) },
  )
}

export function useHariMaga(categoryHint?: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [problem, setProblem] = useState('')
  const [answers, setAnswers] = useState<Record<string, unknown>>({})
  const [pendingField, setPendingField] = useState<string | null>(null)
  const [allowSkip, setAllowSkip] = useState(false)
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  /** The category the backend actually used (shown in the side panel) */
  const [detected, setDetected] = useState<string>()

  const push = (m: NewMessage) =>
    setMessages((prev) => [...prev, { ...m, id: nextId++ } as Message])

  /** Send text + answers to the backend and show whatever comes back. */
  const ask = useCallback(async (text: string, currentAnswers: Record<string, unknown>) => {
    setLoading(true)
    try {
      const data = await routeProblem(text, currentAnswers, categoryHint)
      const r: Routing = data.routing
      setDetected(data.classification.label)

      if (r.status === 'needs_clarification') {
        setPendingField(r.needed_field ?? null)
        setAllowSkip(Boolean(r.allow_skip))
        setPhase('asking')
        push({
          role: 'assistant',
          kind: 'question',
          text: r.question || 'I need one more detail.',
          hint: r.previous_answer_not_understood ? r.hint : undefined,
          options: normalizeOptions(r.options),
          field: r.needed_field,
        })
      } else if (r.status === 'routed' || r.status === 'resolved') {
        setPendingField(null)
        setPhase('done')
        push({ role: 'assistant', kind: 'route', route: normalizeRoute(r, data.classification.label) })
      } else {
        setPendingField(null)
        setPhase('done')
        push({ role: 'assistant', kind: 'error', text: r.message || String(r.status) })
      }
    } catch (err) {
      push({ role: 'assistant', kind: 'error', text: (err as Error).message, code: (err as Error & { code?: string }).code })
    } finally {
      setLoading(false)
    }
  }, [categoryHint])

  /** Called when the user presses Send or taps an option. */
  const submit = useCallback(
    async (value: unknown, label?: string) => {
      if (loading) return
      const shown = label ?? String(value)

      // Answering a clarification question
      if (phase === 'asking' && pendingField) {
        push({ role: 'user', text: shown })
        const next = { ...answers, [pendingField]: value }
        setAnswers(next)
        await ask(problem, next)
        return
      }

      // Starting a brand new problem (after a finished route, clear the old chat)
      const text = String(value).trim()
      if (!text) return
      if (phase === 'done') setMessages([])
      push({ role: 'user', text })
      setProblem(text)
      setAnswers({})
      await ask(text, {})
    },
    [loading, phase, pendingField, answers, problem, ask],
  )

  const reset = useCallback(() => {
    setMessages([])
    setProblem('')
    setAnswers({})
    setPendingField(null)
    setAllowSkip(false)
    setPhase('idle')
    setDetected(undefined)
  }, [])

  return { messages, loading, phase, allowSkip, detected, problem, answers, submit, reset }
}
