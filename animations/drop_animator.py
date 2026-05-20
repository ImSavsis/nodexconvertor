# импорты тут у нас
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal, QObject, Slot
from PySide6.QtWebChannel import QWebChannel
import json


# js-анимация для дроп зоны я пидор
class DropZoneAnimator(QWebEngineView):
    drop_detected = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropAnimator")
        self.setAttribute_flags()

        # канал для общения js <-> python
        self._channel = QWebChannel(self.page())
        self._bridge = _JsBridge()
        self._channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(self._channel)

        self._load_html()

    # def убираем стандартный фон webview
    def setAttribute_flags(self):
        from PySide6.QtCore import Qt
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    # def загружаем html с анимацией
    def _load_html(self):
        html = self._build_html()
        self.setHtml(html)

    # def строим html с canvas-анимацией частиц
    def _build_html(self) -> str:
        return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: transparent; overflow: hidden; }
  canvas { display: block; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
// анимация частиц для дроп зоны

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

window.addEventListener('resize', () => {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});

// настройки частиц
const CONFIG = {
  count: 40,
  speed: 0.4,
  size: { min: 1, max: 3 },
  color: '91, 91, 246',   // accent
  opacity: { idle: 0.15, active: 0.55 },
  connectionDist: 100,
};

let particles = [];
let isActive = false;
let targetOpacity = CONFIG.opacity.idle;
let currentOpacity = CONFIG.opacity.idle;

// def создаём частицу в случайном месте
function makeParticle() {
  return {
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * CONFIG.speed,
    vy: (Math.random() - 0.5) * CONFIG.speed,
    r: CONFIG.size.min + Math.random() * (CONFIG.size.max - CONFIG.size.min),
    o: Math.random() * 0.5 + 0.3,
  };
}

// инициализируем частицы
for (let i = 0; i < CONFIG.count; i++) {
  particles.push(makeParticle());
}

// def рисуем соединения между близкими частицами
function drawConnections(opacity) {
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < CONFIG.connectionDist) {
        const lineOpacity = (1 - dist / CONFIG.connectionDist) * opacity * 0.4;
        ctx.strokeStyle = `rgba(${CONFIG.color}, ${lineOpacity})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.stroke();
      }
    }
  }
}

// def главный цикл анимации
function animate() {
  requestAnimationFrame(animate);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // плавно меняем прозрачность при активации
  currentOpacity += (targetOpacity - currentOpacity) * 0.05;

  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;

    // оборачиваем за край
    if (p.x < 0) p.x = canvas.width;
    if (p.x > canvas.width) p.x = 0;
    if (p.y < 0) p.y = canvas.height;
    if (p.y > canvas.height) p.y = 0;

    // рисуем точку
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${CONFIG.color}, ${p.o * currentOpacity})`;
    ctx.fill();
  }

  drawConnections(currentOpacity);
}

// api для активации из python
window.setActive = function(active) {
  isActive = active;
  targetOpacity = active ? CONFIG.opacity.active : CONFIG.opacity.idle;

  // при активации разгоняем частицы
  if (active) {
    for (const p of particles) {
      p.vx *= 2.5;
      p.vy *= 2.5;
    }
  } else {
    for (const p of particles) {
      p.vx = (Math.random() - 0.5) * CONFIG.speed;
      p.vy = (Math.random() - 0.5) * CONFIG.speed;
    }
  }
};

// def анимация пульса при успешном дропе
window.pulseSuccess = function() {
  let scale = 1;
  let growing = true;
  let frames = 0;

  const pulse = () => {
    if (frames > 30) return;
    frames++;

    if (growing) {
      scale += 0.03;
      if (scale > 1.2) growing = false;
    } else {
      scale -= 0.02;
    }

    for (const p of particles) {
      p.vx *= scale > 1 ? 1.1 : 0.9;
      p.vy *= scale > 1 ? 1.1 : 0.9;
    }
    requestAnimationFrame(pulse);
  };
  pulse();
};

animate();
</script>
</body>
</html>"""


# def мост для вызова методов из js в python
class _JsBridge(QObject):
    @Slot(str)
    def on_event(self, data: str):
        parsed = json.loads(data)
        print(f"[animator bridge] event: {parsed}")
