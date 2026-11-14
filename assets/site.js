"use strict";

const reveal = document.querySelector("[data-reveal]");
const meaning = document.querySelector("#card-meaning");

if (reveal && meaning) {
  reveal.hidden = false;
  meaning.hidden = true;
  reveal.addEventListener("click", () => {
    const expanded = reveal.getAttribute("aria-expanded") === "true";
    reveal.setAttribute("aria-expanded", String(!expanded));
    meaning.hidden = expanded;
    reveal.textContent = expanded ? reveal.dataset.show : reveal.dataset.hide;
  });
}

const tour = document.querySelector("[data-tour]");

if (tour) {
  const steps = [...tour.querySelectorAll("[data-tour-step]")];
  const chapters = [...tour.querySelectorAll("[data-tour-chapter]")];
  const play = tour.querySelector("[data-tour-play]");
  const previous = tour.querySelector("[data-tour-previous]");
  const next = tour.querySelector("[data-tour-next]");
  const restart = tour.querySelector("[data-tour-restart]");
  const status = tour.querySelector("[data-tour-status]");
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  let current = 0;
  let timer = null;
  let revealTimer = null;

  function setComparison(step, revealed) {
    const comparison = step.querySelector("[data-tour-comparison]");
    if (!comparison) return;
    const button = step.querySelector("[data-tour-reveal]");
    comparison.querySelector('[data-tour-state="before"]').hidden = revealed;
    comparison.querySelector('[data-tour-state="after"]').hidden = !revealed;
    button.textContent = revealed ? comparison.dataset.hide : comparison.dataset.show;
    button.setAttribute("aria-pressed", String(revealed));
  }

  function pause() {
    clearTimeout(timer);
    clearTimeout(revealTimer);
    timer = null;
    revealTimer = null;
    play.textContent = tour.dataset.play;
    play.setAttribute("aria-pressed", "false");
    tour.classList.remove("is-playing");
  }

  function show(index, announce = true) {
    current = index;
    steps.forEach((step, number) => { step.hidden = number !== current; });
    chapters.forEach((chapter, number) => {
      if (number === current) chapter.setAttribute("aria-current", "step");
      else chapter.removeAttribute("aria-current");
    });
    previous.disabled = current === 0;
    next.disabled = current === steps.length - 1;
    clearTimeout(revealTimer);
    setComparison(steps[current], false);
    if (timer !== null && !reducedMotion.matches) scheduleReveal();
    if (announce) status.textContent = `${current + 1} / ${steps.length}: ${steps[current].querySelector("h2").textContent}`;
    history.replaceState(null, "", `#tour-step-${current + 1}`);
  }

  function scheduleReveal() {
    clearTimeout(revealTimer);
    if (steps[current].querySelector("[data-tour-comparison]")) {
      revealTimer = setTimeout(() => { setComparison(steps[current], true); }, 3000);
    }
  }

  function schedule() {
    timer = setTimeout(() => {
      if (current === steps.length - 1) {
        pause();
        return;
      }
      show(current + 1);
      if (current === steps.length - 1) pause();
      else schedule();
    }, 9000);
  }

  play.addEventListener("click", () => {
    if (timer !== null) {
      pause();
      return;
    }
    if (current === steps.length - 1) show(0);
    play.textContent = tour.dataset.pause;
    play.setAttribute("aria-pressed", "true");
    tour.classList.add("is-playing");
    schedule();
    if (!reducedMotion.matches) scheduleReveal();
  });
  previous.addEventListener("click", () => { pause(); if (current > 0) show(current - 1); });
  next.addEventListener("click", () => { pause(); if (current < steps.length - 1) show(current + 1); });
  restart.addEventListener("click", () => { pause(); show(0); });
  chapters.forEach((chapter, index) => chapter.addEventListener("click", event => {
    event.preventDefault();
    pause();
    show(index);
  }));
  document.addEventListener("visibilitychange", () => { if (document.hidden) pause(); });
  reducedMotion.addEventListener("change", pause);
  addEventListener("pagehide", pause);
  addEventListener("hashchange", () => {
    const chapter = steps.findIndex(step => `#${step.id}` === location.hash);
    if (chapter >= 0) { pause(); show(chapter); }
  });
  steps.forEach(step => {
    const button = step.querySelector("[data-tour-reveal]");
    if (!button) return;
    button.hidden = false;
    setComparison(step, false);
    button.addEventListener("click", () => {
      pause();
      setComparison(step, button.getAttribute("aria-pressed") !== "true");
    });
  });
  tour.querySelector("[data-tour-toolbar]").hidden = false;
  tour.classList.add("is-enhanced");
  const initial = steps.findIndex(step => `#${step.id}` === location.hash);
  show(initial >= 0 ? initial : 0, false);
}
