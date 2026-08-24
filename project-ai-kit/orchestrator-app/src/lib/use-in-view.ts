import { useEffect, useRef, useState } from "react";

/**
 * True once the referenced element has scrolled into the viewport at least
 * once — then stays true (one-shot reveal, not continuous visibility
 * tracking). Used to defer mermaid rendering (the actually expensive part
 * of a large artifact, not markdown parsing) until a diagram block is
 * about to be seen — AC-E3-19.
 */
export function useInView<T extends HTMLElement>(): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node || inView) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);

    return () => observer.disconnect();
  }, [inView]);

  return [ref, inView];
}
