/*
  TiltCard: a button that tilts in 3D toward the mouse and lifts up.
  Used for the category tiles. Same idea as IslandStage, but smaller.
*/
import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from 'motion/react'
import type { PointerEvent, ReactNode } from 'react'

interface Props {
  children: ReactNode
  onClick: () => void
  selected: boolean
  label: string
}

export function TiltCard({ children, onClick, selected, label }: Props) {
  const reduce = useReducedMotion()
  const px = useMotionValue(0)
  const py = useMotionValue(0)
  const sx = useSpring(px, { stiffness: 220, damping: 18 })
  const sy = useSpring(py, { stiffness: 220, damping: 18 })
  const rotateY = useTransform(sx, [-0.5, 0.5], [-12, 12])
  const rotateX = useTransform(sy, [-0.5, 0.5], [10, -10])

  const onMove = (e: PointerEvent<HTMLButtonElement>) => {
    if (reduce || e.pointerType !== 'mouse') return
    const r = e.currentTarget.getBoundingClientRect()
    px.set((e.clientX - r.left) / r.width - 0.5)
    py.set((e.clientY - r.top) / r.height - 0.5)
  }

  return (
    <div style={{ perspective: 700 }}>
      <motion.button
        type="button"
        aria-pressed={selected}
        aria-label={label}
        onClick={onClick}
        onPointerMove={onMove}
        onPointerLeave={() => {
          px.set(0)
          py.set(0)
        }}
        whileHover={reduce ? undefined : { z: 30, scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
        className={`group relative flex h-full w-full items-center gap-3 rounded-2xl border bg-white/85 p-3 text-left backdrop-blur transition-shadow sm:flex-col sm:items-start sm:p-4 ${
          selected
            ? 'border-forest shadow-[0_18px_40px_-18px_rgb(17_82_63/0.7)] ring-2 ring-forest'
            : 'border-white/70 shadow-[0_10px_30px_-18px_rgb(19_36_30/0.45)] hover:shadow-[0_24px_44px_-20px_rgb(19_36_30/0.55)]'
        }`}
      >
        {children}
      </motion.button>
    </div>
  )
}
