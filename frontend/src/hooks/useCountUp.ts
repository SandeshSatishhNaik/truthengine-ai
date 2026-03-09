"use client";

import { useEffect, useState } from "react";

export function useCountUp(end: number, duration = 1500, start = 0) {
  const [value, setValue] = useState(start);

  useEffect(() => {
    if (end === start) { setValue(start); return; }
    const startTime = performance.now();

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(start + (end - start) * eased));
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }, [end, duration, start]);

  return value;
}
