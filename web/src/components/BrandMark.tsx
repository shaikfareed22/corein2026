import { cx } from "../util";

/**
 * The FOMO logo (docs/brand.md) on its own navy, `public/logo.png`. It stands for the app where
 * the app speaks for itself: the sign-in door, the first seconds before the socket is up, the
 * token gate. Never for the Muse: the face is the Muse, the logo is the app. `size` is the
 * logo's height; it is about two and a half times as wide.
 */
export function BrandMark({ size = 72, className }: { size?: number; className?: string }) {
  const width = Math.round(size * 2.45);
  return (
    <img
      src="/logo.png"
      alt="FOMO"
      width={width}
      height={size}
      draggable={false}
      className={cx("block shrink-0 select-none", className)}
      style={{ width, height: size, borderRadius: Math.round(size * 0.18), objectFit: "contain" }}
    />
  );
}
