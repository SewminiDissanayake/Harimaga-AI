/*
  Composer: the message box fixed at the bottom of the screen.
  Enter = send, Shift+Enter = new line.
*/
import { SendHorizontal } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface Props {
  placeholder: string
  sendLabel: string
  disabled: boolean
  onSend: (text: string) => void
  /** Text put into the box from outside (e.g. tapping an example). */
  prefill?: { text: string; n: number }
}

export function Composer({ placeholder, sendLabel, disabled, onSend, prefill }: Props) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  // When a new prefill arrives (e.g. tapping an example), copy it into the box.
  // React's recommended way: compare with the previous value during render.
  const [lastPrefill, setLastPrefill] = useState(prefill)
  if (prefill !== lastPrefill) {
    setLastPrefill(prefill)
    if (prefill) setText(prefill.text)
  }

  useEffect(() => {
    if (prefill) ref.current?.focus()
  }, [prefill])

  // Grow the textarea with its content, up to ~5 lines
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }, [text])

  const send = () => {
    const value = text.trim()
    if (!value || disabled) return
    onSend(value)
    setText('')
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        send()
      }}
      className="flex items-end gap-2 rounded-2xl border border-line bg-white p-2 shadow-[0_6px_24px_-12px_rgb(19_36_30/0.35)] focus-within:border-forest"
    >
      <label htmlFor="problem" className="sr-only">
        {placeholder}
      </label>
      <textarea
        id="problem"
        ref={ref}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            send()
          }
        }}
        placeholder={placeholder}
        className="max-h-36 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] leading-6 outline-none placeholder:text-muted/80"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="inline-flex h-11 shrink-0 items-center gap-2 rounded-xl bg-forest px-4 font-semibold text-white transition-colors hover:bg-forest-dark disabled:bg-line disabled:text-muted"
      >
        <span className="hidden sm:inline">{sendLabel}</span>
        <SendHorizontal className="size-5" aria-hidden />
        <span className="sr-only sm:hidden">{sendLabel}</span>
      </button>
    </form>
  )
}
