const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");

let dots = [];

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

// create dots
for (let i = 0; i < 120; i++) {
  dots.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * (1.5 * Math.random()) * (1.5 * Math.random()),
    vy: (Math.random() - 0.5) * (1.5 * Math.random()) * (1.5 * Math.random()),
    r: 4,
  });
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let d of dots) {
    d.x += d.vx;
    d.y += d.vy;

    // wrap around edges
    if (d.x < 0) d.x = canvas.width;
    if (d.x > canvas.width) d.x = 0;
    if (d.y < 0) d.y = canvas.height;
    if (d.y > canvas.height) d.y = 0;

    const gradient = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, 5);

    gradient.addColorStop(0.01, "rgba(220,220,220,0.9)");
    gradient.addColorStop(0.7, "rgba(200,200,200,0.1)");
    gradient.addColorStop(1, "rgba(0,0,0,0.0)");

    ctx.fillStyle = gradient;

    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();
  }

  requestAnimationFrame(animate);
}

animate();
