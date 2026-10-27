/**
 * The FOMO logo (docs/brand.md) on its own navy, inline from `fomo-logo.ts` so the bundle fetches
 * nothing. It stands for the app where the app speaks for itself — the sign-in pages, the
 * permissions page — never for the Muse: the face is the Muse, the logo is the app, and the logo
 * never goes in the chat. `size` is the logo's height; it is about two and a half times as wide.
 */
import { createElement as h, type ReactNode } from 'react'
import { FOMO_LOGO } from './fomo-logo.ts'

export function BrandMark({ size = 72, className }: { size?: number; className?: string }): ReactNode {
  const width = Math.round(size * 2.45)
  return h('img', {
    src: FOMO_LOGO,
    width,
    height: size,
    alt: 'FOMO',
    draggable: false,
    className: `nm-brand-mark${className ? ` ${className}` : ''}`,
    style: { width, height: size, borderRadius: Math.round(size * 0.18), objectFit: 'contain', display: 'block' },
  })
}
