/**
 * The Zeph mark: an open circle with an orange dot.
 *
 * @param props - `size` in pixels and the stroke `color`.
 * @returns The logo SVG.
 */
export function ZephLogo({
  size = 26,
  color = "currentColor",
}: {
  size?: number;
  color?: string;
}) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" aria-hidden="true">
      <path
        d="M22.66 9 A10 10 0 1 1 17.42 4.6"
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <circle cx="20.4" cy="6.3" r="1.7" fill="var(--color-orange)" />
    </svg>
  );
}
