/** 설명 카드가 강조 대상을 가리지 않는 빈 공간을 찾고 말풍선 꼬리를 대상에 맞춘다. */
export type Rect = { x: number; y: number; w: number; h: number };
export function placeGuide(
  target: Rect,
  card: { w: number; h: number },
  viewport: { w: number; h: number },
  preferred?: "below-left" | "below-right",
) {
  const margin = 16,
    gap = 20,
    cx = target.x + target.w / 2,
    cy = target.y + target.h / 2;
  const clamp = (v: number, min: number, max: number) =>
    Math.max(min, Math.min(v, Math.max(min, max)));
  const candidates = [
    {
      side: "left",
      x: target.x + target.w + gap,
      y: clamp(cy - card.h / 2, margin, viewport.h - card.h - margin),
    },
    {
      side: "right",
      x: target.x - card.w - gap,
      y: clamp(cy - card.h / 2, margin, viewport.h - card.h - margin),
    },
    {
      side: "top",
      x: clamp(cx - card.w / 2, margin, viewport.w - card.w - margin),
      y: target.y + target.h + gap,
    },
    {
      side: "bottom",
      x: clamp(cx - card.w / 2, margin, viewport.w - card.w - margin),
      y: target.y - card.h - gap,
    },
  ];
  if (preferred)
    candidates.unshift({
      side: "top",
      x: clamp(
        preferred === "below-left" ? target.x : target.x + target.w - card.w,
        margin,
        viewport.w - card.w - margin,
      ),
      y: target.y + target.h + gap,
    });
  const valid = candidates.find(
    (p) =>
      p.x >= margin &&
      p.y >= margin &&
      p.x + card.w <= viewport.w - margin &&
      p.y + card.h <= viewport.h - margin,
  );
  const chosen =
    valid ??
    candidates.reduce((a, b) => {
      const overflow = (p: typeof a) =>
        Math.max(0, margin - p.x) +
        Math.max(0, margin - p.y) +
        Math.max(0, p.x + card.w + margin - viewport.w) +
        Math.max(0, p.y + card.h + margin - viewport.h);
      return overflow(a) <= overflow(b) ? a : b;
    });
  const left = clamp(chosen.x, margin, viewport.w - card.w - margin),
    top = clamp(chosen.y, margin, viewport.h - card.h - margin);
  return {
    left,
    top,
    side: chosen.side,
    arrow: clamp(
      chosen.side === "left" || chosen.side === "right" ? cy - top : cx - left,
      24,
      (chosen.side === "left" || chosen.side === "right" ? card.h : card.w) -
        24,
    ),
    separate: !!valid,
  };
}
