let outer = document.querySelector(".content");
let inner = null;

function initScrollSystem() {
  outer = document.querySelector(".content");
  inner = document.querySelector(".home-content");

  if (!outer || !inner) return;

  function updateScrollState() {
    const atBottom =
      outer.scrollTop + outer.clientHeight >= outer.scrollHeight - 1;

    if (atBottom) {
      inner.style.overflowY = "scroll";
    } else {
      inner.style.overflowY = "hidden";
      inner.scrollTop = 0;
    }
  }

  // remove old listener to avoid duplicates
  outer.removeEventListener("scroll", updateScrollState);

  outer.addEventListener("scroll", updateScrollState);
  updateScrollState();
}

// initial load
document.addEventListener("DOMContentLoaded", initScrollSystem);

// AFTER HTMX swaps content
document.body.addEventListener("htmx:afterSwap", initScrollSystem);

// spotlight effect

let mouseX = 0;
let mouseY = 0;

document.addEventListener("mousemove", (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;

  document
    .querySelectorAll(".pannel-wrapper, .home-content, .home-content-wrapper")
    .forEach((el) => {
      const rect = el.getBoundingClientRect();

      const x = mouseX - rect.left;
      const y = mouseY - rect.top;

      el.style.setProperty("--x", `${x}px`);
      el.style.setProperty("--y", `${y}px`);
    });
});

// selector highlight

const items = document.querySelectorAll(".menu-item");
const highlight = document.querySelector(".menu-highlight");

function move(el) {
  if (!el) return;
  highlight.style.transform = `translateY(${el.offsetTop}px)`;
}

function setActiveFromUrl() {
  const path = window.location.pathname;

  items.forEach((item) => {
    item.classList.remove("active");
  });

  let active = items[0];

  items.forEach((item) => {
    const page = item.dataset.page;

    if ((path === "/" && page === "home") || path.includes(page)) {
      active = item;
    }
  });

  active.classList.add("active");
  move(active);
}

// initial load
document.addEventListener("DOMContentLoaded", setActiveFromUrl);

// after HTMX swaps
document.body.addEventListener("htmx:afterSwap", setActiveFromUrl);
