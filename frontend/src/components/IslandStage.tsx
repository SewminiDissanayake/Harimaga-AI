/*
  IslandStage: the 3D hero illustration.

  How the 3D works (no WebGL needed):
    - The outer div sets `perspective`, which gives depth to children.
    - The stage div uses `transform-style: preserve-3d` so each layer can sit
      at a different depth with translateZ (sea rings low, island high, pin highest).
    - Moving the mouse changes rotateX / rotateY, so the whole scene tilts.
      `useSpring` smooths the movement so it feels physical.
    - With "reduce motion" turned on in the OS, everything stays still.
*/
import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from 'motion/react'
import type { PointerEvent } from 'react'

export function IslandStage({ size = 320 }: { size?: number }) {
  const reduce = useReducedMotion()

  // Pointer position from -0.5 to 0.5
  const px = useMotionValue(0)
  const py = useMotionValue(0)
  const sx = useSpring(px, { stiffness: 120, damping: 14 })
  const sy = useSpring(py, { stiffness: 120, damping: 14 })
  const rotateY = useTransform(sx, [-0.5, 0.5], [-18, 18])
  const rotateX = useTransform(sy, [-0.5, 0.5], [16, -8])

  const onMove = (e: PointerEvent<HTMLDivElement>) => {
    if (reduce) return
    const r = e.currentTarget.getBoundingClientRect()
    px.set((e.clientX - r.left) / r.width - 0.5)
    py.set((e.clientY - r.top) / r.height - 0.5)
  }
  const onLeave = () => {
    px.set(0)
    py.set(0)
  }

  return (
    <div
      className="relative select-none"
      style={{ width: size, height: size, perspective: 900 }}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      aria-hidden
    >
      <motion.div
        className="absolute inset-0"
        style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
        initial={reduce ? false : { rotateX: 40, opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.9, ease: [0.2, 0.8, 0.2, 1] }}
      >
        {/* Sea plate, lying flat, far back */}
        <div
          className="absolute inset-[6%] rounded-full bg-[radial-gradient(circle_at_40%_35%,#3fb6c9_0%,#13798d_55%,#0b4f5f_100%)] shadow-[0_40px_80px_-20px_rgb(0_0_0/0.55)]"
          style={{ transform: 'translateZ(-40px)' }}
        />

        {/* Ripples spreading out from the island */}
        {!reduce &&
          [0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-[22%] rounded-full border-2 border-white/35"
              style={{ transform: 'translateZ(-20px)' }}
              animate={{ scale: [0.7, 1.45], opacity: [0.7, 0] }}
              transition={{ duration: 4.5, repeat: Infinity, delay: i * 1.5, ease: 'easeOut' }}
            />
          ))}

        {/* Island, floating */}
        <motion.img
          src="/island.svg"
          alt=""
          draggable={false}
          className="absolute inset-[4%] drop-shadow-[0_30px_25px_rgb(0_0_0/0.35)]"
          style={{ transform: 'translateZ(50px)' }}
          animate={reduce ? undefined : { y: [0, -10, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        />

        {/* Glow at the destination: the authority */}
        {!reduce && (
          <motion.div
            className="absolute size-10 rounded-full bg-saffron/60 blur-md"
            style={{ left: '46%', top: '78%', transform: 'translateZ(90px)' }}
            animate={{ scale: [1, 1.6, 1], opacity: [0.8, 0.2, 0.8] }}
            transition={{ duration: 2.4, repeat: Infinity }}
          />
        )}
      </motion.div>
    </div>
  )
}
