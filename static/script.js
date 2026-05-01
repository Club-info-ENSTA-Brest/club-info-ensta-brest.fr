const outer = document.querySelector(".content");
const inner = document.querySelector(".home-content");

function updateScrollState() {
  const atBottom =
    outer.scrollTop + outer.clientHeight >= outer.scrollHeight - 1;

  if (atBottom) {
    inner.style.overflowY = "scroll";
  } else {
    inner.style.overflowY = "hidden";
    inner.scrollTop = 0; // optional: reset inner scroll
  }
}

outer.addEventListener("scroll", updateScrollState);
window.addEventListener("load", updateScrollState);

// spotlight effect

let mouseX = 0;
let mouseY = 0;

document.addEventListener("mousemove", (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;

  document.querySelectorAll(".pannel-wrapper, .home-content").forEach((el) => {
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
const menu = document.querySelector(".pannel-menu");

function moveHighlight(el) {
  const offset = el.offsetTop;
  highlight.style.transform = `translateY(${offset}px)`;
}

// init (Home par défaut)
moveHighlight(items[0]);
items[0].classList.add("active");

items.forEach((item) => {
  item.addEventListener("click", () => {
    items.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
    moveHighlight(item);
  });
});
