"""
Conjectura de Collatz — app em Streamlit
----------------------------------------
Como rodar:
    pip install streamlit
    streamlit run conjectura_de_collatz_app.py

Aceita números enormes (milhares de dígitos), digitados por extenso
ou como potência: 2^500, 10^100, 3^200+1, 2**64-1.
"""
import json
import math
import re
import sys
import time

import streamlit as st
import streamlit.components.v1 as components

# Python 3.11+ limita a conversão int <-> texto a 4300 dígitos; liberamos.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)

# ============================================================
# Configuração
# ============================================================
st.set_page_config(page_title="Conjectura de Collatz", page_icon="⛰️", layout="wide")

CORES = {
    "noite": "#0a1324", "painel": "#111d33", "linha": "#22334f", "texto": "#e7ecf4", "suave": "#8797b1",
    "par": "#6ec6da", "impar": "#f2b35a", "um": "#93d48b", "pico": "#ff6b5e", "brilho": "#f8e6b8",
}
FAMOSOS = ["27", "871", "77031", "2^100+1", "10^50", "3^500"]
MAX_DIGITOS = 20_000          # limite de segurança da entrada
MAX_PASSOS = 5_000_000        # nenhuma trajetória conhecida chega perto disso
MAX_PONTOS_GRAFICO = 3_000    # acima disso, o gráfico é amostrado (o pico sempre entra)
MAX_CHIPS = 400               # o diário mostra início e fim quando a trilha é maior
DURACAO_MAX = {"lento": 60_000, "normal": 25_000, "rápido": 10_000}   # ms da animação inteira
MS_POR_PASSO = {"lento": 520, "normal": 200, "rápido": 55}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=JetBrains+Mono:wght@400;600&display=swap');
.stApp {{ background: {CORES['noite']}; color: {CORES['texto']}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {CORES['painel']}; border-right: 1px solid {CORES['linha']}; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] label p {{ color: {CORES['texto']} !important; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color: {CORES['suave']} !important; }}
/* campo do número */
[data-testid="stTextInput"] input {{ background: {CORES['noite']} !important; color: {CORES['brilho']} !important;
  font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 600; caret-color: {CORES['brilho']}; }}
[data-testid="stTextInput"] div[data-baseweb="input"], [data-testid="stTextInput"] div[data-baseweb="base-input"] {{
  background: {CORES['noite']} !important; border-color: {CORES['linha']} !important; }}
/* botões das trilhas famosas */
[data-testid="stSidebar"] .stButton button {{ background: transparent !important; color: {CORES['texto']} !important;
  border: 1px solid {CORES['linha']} !important; font-family: 'JetBrains Mono', monospace; }}
[data-testid="stSidebar"] .stButton button p {{ color: inherit !important; font-family: 'JetBrains Mono', monospace; font-size: 13px; }}
[data-testid="stSidebar"] .stButton button:hover {{ color: {CORES['brilho']} !important; border-color: {CORES['brilho']} !important; }}
/* exemplos em código */
[data-testid="stSidebar"] code {{ background: {CORES['noite']} !important; color: {CORES['brilho']} !important; }}
/* tabela e expansor na área principal */
[data-testid="stExpander"] details {{ background: {CORES['painel']}; border-color: {CORES['linha']}; }}
[data-testid="stExpander"] summary p {{ color: {CORES['texto']} !important; }}
.stApp p, .stApp label {{ color: {CORES['texto']}; }}
h1, h2, h3 {{ font-family: 'Archivo', sans-serif !important; font-stretch: 70%; font-weight: 800 !important; color: {CORES['texto']} !important; }}
.block-container {{ padding-top: 1.2rem; max-width: 1280px; }}
.lbl {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: {CORES['suave']}; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1px; background: {CORES['linha']};
          border: 1px solid {CORES['linha']}; border-radius: 12px; overflow: hidden; }}
.stat {{ background: {CORES['painel']}; padding: 14px 18px; display: grid; gap: 2px; min-width: 0; }}
.stat .v {{ font-family: 'Archivo', sans-serif; font-stretch: 70%; font-weight: 800; font-size: 30px; line-height: 1.1; overflow-wrap: anywhere; }}
.stat small {{ color: {CORES['suave']}; font-size: 12px; }}
.trilha {{ display: flex; flex-wrap: wrap; gap: 6px 4px; align-items: center; max-height: 280px; overflow-y: auto;
           background: {CORES['painel']}; border: 1px solid {CORES['linha']}; border-radius: 12px; padding: 14px; }}
.no {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; padding: 2px 9px; border-radius: 99px; border: 1px solid currentColor; }}
.no.pk {{ box-shadow: 0 0 0 2px {CORES['pico']}; }}
.seta {{ color: {CORES['linha']}; font-size: 12px; }}
.corte {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {CORES['suave']}; padding: 0 8px; }}
.legenda {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; color: {CORES['suave']}; margin-bottom: 8px; }}
.legenda i {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# Matemática (inteiros de precisão ilimitada do Python)
# ============================================================
SUPER = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def interpretar(texto: str) -> int:
    """Lê '27', '1.000.000', '2^500', '10**100', '3^200+1', '2^64-1'."""
    t = texto.strip().replace(" ", "").replace("_", "").replace("**", "^")
    m = re.fullmatch(r"(\d+)\^(\d+)([+-]\d+)?", t)
    if m:
        base, exp, ajuste = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        if exp * math.log10(max(base, 2)) > MAX_DIGITOS:
            raise ValueError(f"Esse número passa de {MAX_DIGITOS:,} dígitos.".replace(",", "."))
        return base ** exp + ajuste
    t = t.replace(".", "")
    if not re.fullmatch(r"\d+", t):
        raise ValueError("Use só dígitos, ou uma potência como 2^500 ou 10^100+7.")
    if len(t) > MAX_DIGITOS:
        raise ValueError(f"Use até {MAX_DIGITOS:,} dígitos.".replace(",", "."))
    return int(t)


@st.cache_data(show_spinner=False, max_entries=20)
def collatz(n: int) -> list[int]:
    """Sequência de Collatz de n até 1, com operações de bits (rápido mesmo com milhares de dígitos)."""
    seq = [n]
    while n != 1:
        n = n >> 1 if n & 1 == 0 else 3 * n + 1
        seq.append(n)
        if len(seq) > MAX_PASSOS:
            raise RuntimeError("limite de passos")
    return seq


def digitos(v: int) -> int:
    return len(str(v)) if v < 10**4000 else int(log10_int(v)) + 1


def fmt(v: int) -> str:
    """Formato brasileiro curto: 9.232 | 1,2346·10⁴⁵ para números gigantes."""
    if v < 10**15:
        return f"{v:,}".replace(",", ".")
    s = str(v) if v < 10**4000 else None
    if s is None:  # muito grande: mantissa via logaritmo (só para exibição)
        lg = log10_int(v)
        e = int(lg)
        mant = 10 ** (lg - e)
        return f"{mant:.4f}".replace(".", ",") + "·10" + str(e).translate(SUPER)
    return f"{s[0]},{s[1:5]}·10" + str(len(s) - 1).translate(SUPER)


def log10_int(v: int) -> float:
    """log10 preciso mesmo para inteiros com milhares de dígitos."""
    if v < 10**300:
        return math.log10(v)
    s = v.bit_length() - 64
    return math.log10(v >> s) + s * math.log10(2)


def paridade(v: int) -> int:
    return 2 if v == 1 else v & 1        # 0 par, 1 ímpar, 2 chegada


def op_html(seq: list[int], i: int) -> str:
    v = seq[i]
    cls = ["e", "o", "one"][paridade(v)]
    if i == 0:
        return f'partida em <span class="{cls}">{fmt(v)}</span>'
    p = seq[i - 1]
    if p & 1 == 0:
        txt = f'<span class="e">{fmt(p)}</span> é par → ÷ 2 = <span class="{cls}">{fmt(v)}</span>'
    else:
        txt = f'<span class="o">{fmt(p)}</span> é ímpar → 3n + 1 = <span class="{cls}">{fmt(v)}</span>'
    return txt + (' <span class="one">· chegou no 1</span>' if v == 1 else "")


def op_curta(seq: list[int], i: int) -> str:
    if i == 0:
        return "partida"
    return "÷ 2" if seq[i - 1] & 1 == 0 else "3n + 1"


def amostrar(seq: list[int], pico_idx: int) -> list[int]:
    """Índices para o gráfico: todos, ou uma amostra regular que inclui o pico e o fim."""
    total = len(seq)
    if total <= MAX_PONTOS_GRAFICO:
        return list(range(total))
    passo = (total - 1) / (MAX_PONTOS_GRAFICO - 1)
    idx = {round(k * passo) for k in range(MAX_PONTOS_GRAFICO)} | {0, pico_idx, total - 1}
    return sorted(idx)


# ============================================================
# Barra lateral
# ============================================================
if "entrada" not in st.session_state:
    st.session_state.entrada = "27"


def escolher(v: str):
    st.session_state.entrada = v


with st.sidebar:
    st.markdown("## ⛰️ Conjectura de Collatz")
    st.caption("**Regra:** se o número é par, divide por 2 (desce); se é ímpar, faz 3n + 1 (sobe). "
               "A conjectura diz que toda trilha termina no 1.")
    st.divider()
    st.markdown('<span class="lbl">Número inicial</span>', unsafe_allow_html=True)
    texto = st.text_input("Número inicial", key="entrada", label_visibility="collapsed",
                          help="Aceita números enormes e potências: 2^500, 10^100+7, 2**64-1")

    st.markdown('<span class="lbl">Trilhas famosas</span>', unsafe_allow_html=True)
    cols = st.columns(3)
    for k, v in enumerate(FAMOSOS):
        cols[k % 3].button(v, key=f"fam{k}", on_click=escolher, args=(v,), width="stretch")

    st.divider()
    velocidade = st.select_slider("Velocidade da escalada", options=["lento", "normal", "rápido"], value="normal")

try:
    n = interpretar(texto)
    if n < 1:
        raise ValueError("Use um número inteiro positivo.")
except ValueError as e:
    st.error(str(e))
    st.stop()

t0 = time.perf_counter()
try:
    seq = collatz(n)
except RuntimeError:
    st.error(f"A trilha passou de {fmt(MAX_PASSOS)} passos e o cálculo foi interrompido.")
    st.stop()
tempo_calc = time.perf_counter() - t0

passos = len(seq) - 1
pico = max(seq)
pico_idx = seq.index(pico)
impares = sum(v & 1 for v in seq[:-1])
pares = passos - impares
idx = amostrar(seq, pico_idx)

# escala vertical automática: log quando o pico é muito maior que o início ou gigantesco
escala_js = "log" if (log10_int(pico) - log10_int(n) > 2.7 and len(seq) > 60) or digitos(pico) > 15 else "lin"
ms = max(4.0, min(MS_POR_PASSO[velocidade], DURACAO_MAX[velocidade] / max(1, len(idx) - 1)))


# ============================================================
# Cena animada (canvas em HTML/JS)
# ============================================================
CENA_HTML = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
  :root { --night:#0a1324; --panel:#111d33; --line:#22334f; --ink:#e7ecf4; --muted:#8797b1;
          --even:#6ec6da; --odd:#f2b35a; --one:#93d48b; --peak:#ff6b5e; --glow:#f8e6b8; color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body { margin:0; background: var(--night); color: var(--ink); font-family: Archivo, system-ui, sans-serif; }
  .scene { position: relative; border-radius: 14px; overflow: hidden; border: 1px solid var(--line); }
  canvas { display:block; width:100%; height:520px; }
  .txt { position:absolute; top:22px; left:24px; right:24px; pointer-events:none; display:grid; gap:6px; }
  .eyebrow, .lbl { font-family:"JetBrains Mono", monospace; font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
  h1 { margin:0; font-stretch:66%; font-weight:800; font-size:clamp(34px,6vw,68px); line-height:.92; text-shadow:0 2px 24px rgba(10,19,36,.8); }
  h1 em { font-style:normal; color:var(--glow); }
  .rule { font-family:"JetBrains Mono", monospace; font-size:13px; color:var(--muted); display:flex; flex-wrap:wrap; gap:4px 16px; }
  .e{color:var(--even)} .o{color:var(--odd)} .one{color:var(--one)}
  #tip { position:absolute; pointer-events:none; background:rgba(10,19,36,.92); border:1px solid var(--line); font-family:"JetBrains Mono", monospace;
         font-size:12px; padding:5px 10px; border-radius:6px; white-space:nowrap; transform:translate(-50%, calc(-100% - 14px)); }
  .bar { margin-top:12px; background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:14px 16px; display:grid; gap:12px; }
  .row { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:10px 20px; }
  #op { font-family:"JetBrains Mono", monospace; font-size:clamp(15px,2.2vw,20px); font-weight:600; overflow-wrap:anywhere; }
  .player { display:flex; gap:10px; }
  button { font:inherit; color:var(--ink); cursor:pointer; width:42px; height:42px; border-radius:50%; border:1px solid var(--line); background:transparent; }
  button:hover { border-color:var(--glow); }
  button.primary { background:var(--glow); color:var(--night); border-color:var(--glow); }
  #scrub { width:100%; accent-color:var(--odd); }
  .note { font-family:"JetBrains Mono", monospace; font-size:11px; color:var(--muted); }
  [hidden]{display:none!important}
</style>

<div class="scene">
  <canvas id="sky"></canvas>
  <div class="txt">
    <h1>Conjectura de <em>Collatz</em></h1>
  </div>
  <div id="tip" hidden></div>
</div>
<div class="bar">
  <div class="row">
    <div style="min-width:0;flex:1 1 300px"><div class="lbl" id="stepLbl">Passo 0</div><div id="op">—</div></div>
    <div class="player">
      <button id="restart" title="Recomeçar">⟲</button>
      <button id="play" class="primary" title="Pausar">❚❚</button>
      <button id="end" title="Ir ao fim">⇥</button>
    </div>
  </div>
  <input id="scrub" type="range" min="0" value="0">
  <div class="note" id="note" hidden></div>
</div>

<script>
(() => {
  const D = __DATA__;
  // Arrays paralelos, um item por ponto desenhado:
  // I = número do passo, LIN = valor/pico, LG = log10(valor)/log10(pico), PAR = 0 par / 1 ímpar / 2 chegada, S = rótulo, OP = operação
  const { I, LIN, LG, PAR, S, OP } = D;
  const N = I.length - 1, totalSteps = D.steps, peakIdx = D.peak, stepMs = D.ms, scale = D.scale;
  const $ = (id) => document.getElementById(id);
  const cv = $('sky'), ctx = cv.getContext('2d'), tip = $('tip'), scrub = $('scrub');
  const C = { night2:'#13223c', night:'#0a1324', even:'#6ec6da', odd:'#f2b35a', one:'#93d48b', peak:'#ff6b5e', glow:'#f8e6b8' };
  const COL = [C.even, C.odd, C.one];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const strip = (h) => h.replace(/<[^>]+>/g, '');
  function rng(s) { return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  if (D.sampled) { $('note').hidden = false; $('note').textContent = `Trilha longa: o gráfico mostra ${N + 1} de ${totalSteps + 1} pontos (o pico sempre incluído).`; }

  let prog = reduce ? N : 0, playing = !reduce && N > 0, geo, scenery, lastStep = -1;
  scrub.max = N;

  function layout() {
    const dpr = Math.min(2, devicePixelRatio || 1), W = cv.clientWidth, H = cv.clientHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); ctx.setTransform(dpr,0,0,dpr,0,0);
    const narrow = W < 560;
    const m = { l: narrow ? 52 : 84, r: narrow ? 22 : 56, t: narrow ? 120 : 130, b: 52 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b, base = H - m.b;
    const Y = scale === 'log' ? LG : LIN;
    const y = (k) => base - Y[k] * ih * .96;
    const ticks = scale === 'log' ? D.ticksLog : D.ticksLin;   // [fração, rótulo]
    const x = (k) => m.l + (totalSteps === 0 ? iw / 2 : (I[k] / totalSteps) * iw);
    const P = I.map((_, k) => [x(k), y(k)]);
    const K = N > 1500 ? 1 : N > 600 ? 2 : N > 250 ? 4 : 10;
    const d = [], ms = [];
    for (let i = 0; i < N; i++) d.push(P[i+1][1] - P[i][1]);
    for (let i = 0; i <= N; i++) ms.push(i === 0 ? (d[0] || 0) : i === N ? d[N-1] : (d[i-1] * d[i] <= 0 ? 0 : (d[i-1] + d[i]) / 2));
    const curve = [];
    for (let i = 0; i < N; i++) {
      const [x0, y0] = P[i], [x1, y1] = P[i+1];
      for (let k = 0; k < K; k++) {
        const t = k / K, a = 2*t*t*t - 3*t*t + 1, b = t*t*t - 2*t*t + t, c = -2*t*t*t + 3*t*t, e = t*t*t - t*t;
        curve.push([x0 + (x1 - x0) * t, a*y0 + b*ms[i] + c*y1 + e*ms[i+1]]);
      }
    }
    curve.push(P[N]);
    geo = { W, H, m, iw, ih, base, ticks, P, curve, K, spacing: N ? iw / N : iw, narrow };

    const r = rng(7), stars = [];
    for (let i = 0; i < Math.round(W * H / 2600); i++) stars.push({ x: r()*W, y: r()*base*.95, s: r()*1.3+.3, p: r()*6.28, f: .6 + r()*1.8 });
    const ridges = [[.50,.10,'#16264280',9],[.62,.08,'#1a2c4ccc',13],[.74,.06,'#152440',19]].map(([top, amp, col, seg]) => {
      const pts = []; for (let i = 0; i <= seg; i++) pts.push([(i/seg)*W, Math.min(base, H*top + (r()-.5)*2*H*amp*(i%2 ? 1 : .35))]);
      return { pts, col };
    });
    const trees = []; for (let i = 0; i < Math.round(W / 9); i++) trees.push({ x: r()*W, h: 10 + r()*26, w: 5 + r()*6 });
    scenery = { stars, ridges, trees, moon: { x: W*.86, y: 92, r: Math.max(20, Math.min(34, W*.03)) }, shoot: null, next: 2500 };
  }

  function rr(x, y, w, h, r) { ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); }

  function draw(t) {
    const { W, H, m, ih, base, ticks, P, curve, K, spacing, narrow } = geo;
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#060c1a'); g.addColorStop(.55, C.night2); g.addColorStop(1, '#1b2b48');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    for (const s of scenery.stars) {
      ctx.globalAlpha = reduce ? .7 : .45 + .45 * Math.sin(t/1000*s.f + s.p);
      ctx.fillStyle = '#dfe8ff'; ctx.beginPath(); ctx.arc(s.x, s.y, s.s, 0, 6.283); ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (!reduce) {
      scenery.next -= 16;
      if (!scenery.shoot && scenery.next <= 0) { scenery.shoot = { x: Math.random()*W*.6 + W*.1, y: Math.random()*base*.3 + 20, life: 0 }; scenery.next = 5000 + Math.random()*7000; }
      const sh = scenery.shoot;
      if (sh) {
        sh.life += 16; const k = sh.life / 900, hx = sh.x + k*260, hy = sh.y + k*110;
        const tg = ctx.createLinearGradient(hx, hy, hx-90, hy-38);
        tg.addColorStop(0, `rgba(248,230,184,${1-k})`); tg.addColorStop(1, 'rgba(248,230,184,0)');
        ctx.strokeStyle = tg; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(hx-90, hy-38); ctx.stroke();
        if (k >= 1) scenery.shoot = null;
      }
    }
    const mo = scenery.moon;
    const mg = ctx.createRadialGradient(mo.x, mo.y, mo.r*.6, mo.x, mo.y, mo.r*3.2);
    mg.addColorStop(0, 'rgba(248,230,184,.18)'); mg.addColorStop(1, 'rgba(248,230,184,0)');
    ctx.fillStyle = mg; ctx.beginPath(); ctx.arc(mo.x, mo.y, mo.r*3.2, 0, 6.283); ctx.fill();
    ctx.save(); ctx.beginPath(); ctx.arc(mo.x, mo.y, mo.r, 0, 6.283); ctx.clip();
    ctx.fillStyle = C.glow; ctx.fillRect(mo.x-mo.r, mo.y-mo.r, mo.r*2, mo.r*2);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(mo.x + mo.r*.45, mo.y - mo.r*.25, mo.r*.92, 0, 6.283); ctx.fill(); ctx.restore();
    for (const R of scenery.ridges) { ctx.fillStyle = R.col; ctx.beginPath(); ctx.moveTo(0, H); for (const [a, b] of R.pts) ctx.lineTo(a, b); ctx.lineTo(W, H); ctx.closePath(); ctx.fill(); }

    // eixo de altitude
    ctx.font = '11px "JetBrains Mono", monospace'; ctx.textBaseline = 'middle';
    for (const [f, lab] of ticks) {
      const yy = Math.round(base - f * ih * .96) + .5;
      ctx.strokeStyle = 'rgba(135,151,177,.16)'; ctx.setLineDash([2, 6]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(m.l, yy); ctx.lineTo(W - m.r, yy); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(135,151,177,.85)'; ctx.textAlign = 'right'; ctx.fillText(lab, m.l - 10, yy);
    }

    // montanha se desenhando
    const idx = Math.min(curve.length - 1, Math.floor(prog * K)), frac = prog * K - idx;
    const pts = curve.slice(0, idx + 1);
    if (idx < curve.length - 1 && frac > 0) { const a = curve[idx], b = curve[idx+1]; pts.push([a[0] + (b[0]-a[0])*frac, a[1] + (b[1]-a[1])*frac]); }
    const head = pts[pts.length - 1];
    if (pts.length > 1) {
      const fg = ctx.createLinearGradient(0, m.t, 0, base);
      fg.addColorStop(0, 'rgba(214,230,248,.55)'); fg.addColorStop(.25, 'rgba(120,160,205,.30)'); fg.addColorStop(1, 'rgba(20,36,64,.95)');
      ctx.fillStyle = fg; ctx.beginPath(); ctx.moveTo(pts[0][0], base); for (const p of pts) ctx.lineTo(p[0], p[1]); ctx.lineTo(head[0], base); ctx.closePath(); ctx.fill();
      ctx.save(); ctx.shadowColor = C.glow; ctx.shadowBlur = 14; ctx.strokeStyle = C.glow; ctx.lineWidth = N > 1500 ? 1.4 : 2.2; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (const p of pts) ctx.lineTo(p[0], p[1]); ctx.stroke(); ctx.restore();
    }
    for (const tr of scenery.trees) {
      ctx.fillStyle = tr.h > 26 ? '#0a1426' : '#0e1a30';
      ctx.beginPath(); ctx.moveTo(tr.x - tr.w, base + 2); ctx.lineTo(tr.x, base + 2 - tr.h); ctx.lineTo(tr.x + tr.w, base + 2); ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle = '#0a1426'; ctx.fillRect(0, base + 1, W, H - base);

    // marcos de passo no chão
    const every = Math.max(1, Math.ceil(totalSteps / (narrow ? 5 : 10)));
    const mag = Math.pow(10, Math.floor(Math.log10(every)));
    const step = [1, 2, 2.5, 5, 10].map(k => k * mag).find(s => s >= every);
    ctx.textAlign = 'center'; ctx.fillStyle = 'rgba(135,151,177,.7)';
    for (let s = 0; s <= totalSteps; s += step) ctx.fillText(Math.round(s).toLocaleString('pt-BR'), m.l + (totalSteps ? s / totalSteps : .5) * geo.iw, base + 24);
    ctx.textAlign = 'right'; ctx.fillText('passos →', W - m.r, base + 40);

    // nós alcançados
    const reached = Math.floor(prog + 1e-6);
    if (spacing >= 2.5) {
      const r = Math.max(1.4, Math.min(4.5, spacing * .28));
      for (let i = 0; i <= reached; i++) { ctx.fillStyle = COL[PAR[i]]; ctx.beginPath(); ctx.arc(P[i][0], P[i][1], r, 0, 6.283); ctx.fill(); }
    }
    if (spacing >= 40) {
      ctx.font = '600 10px "JetBrains Mono", monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = 'rgba(231,236,244,.75)';
      for (let i = 0; i < reached; i++) { const up = i === 0 || P[i][1] <= P[i-1][1]; ctx.fillText(S[i], P[i][0], P[i][1] + (up ? -10 : 18)); }
    }
    // bandeira no pico
    if (reached >= peakIdx && N > 0) {
      const [px, py] = P[peakIdx], left = px > W - m.r - 170, wave = reduce ? 0 : Math.sin(t/260) * 2;
      ctx.strokeStyle = C.peak; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(px, py-3); ctx.lineTo(px, py-34); ctx.stroke();
      ctx.fillStyle = C.peak; ctx.beginPath(); ctx.moveTo(px, py-34); ctx.lineTo(px + (left ? -17 : 17), py-29+wave); ctx.lineTo(px, py-23); ctx.closePath(); ctx.fill();
      ctx.font = '600 12px "JetBrains Mono", monospace'; ctx.textAlign = left ? 'right' : 'left'; ctx.textBaseline = 'middle';
      ctx.fillText(`pico ${S[peakIdx]}`, px + (left ? -22 : 22), py - 30);
    }
    // lanterna
    const cur = Math.min(N, reached), hc = COL[PAR[cur]], pulse = reduce ? 1 : 1 + .18 * Math.sin(t/220);
    const lg = ctx.createRadialGradient(head[0], head[1], 0, head[0], head[1], 26*pulse);
    lg.addColorStop(0, 'rgba(248,230,184,.55)'); lg.addColorStop(1, 'rgba(248,230,184,0)');
    ctx.fillStyle = lg; ctx.beginPath(); ctx.arc(head[0], head[1], 26*pulse, 0, 6.283); ctx.fill();
    ctx.fillStyle = hc; ctx.strokeStyle = C.night; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(head[0], head[1], 5.5, 0, 6.283); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = 'rgba(248,230,184,.25)'; ctx.setLineDash([3,4]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(head[0], head[1] + 8); ctx.lineTo(head[0], base); ctx.stroke(); ctx.setLineDash([]);
    const label = S[cur]; ctx.font = '600 13px "JetBrains Mono", monospace';
    const tw = ctx.measureText(label).width + 16;
    const lx = Math.min(Math.max(head[0], m.l + tw/2), W - 8 - tw/2); let ly = head[1] - 22; if (ly < 18) ly = head[1] + 30;
    ctx.fillStyle = 'rgba(6,12,26,.85)'; ctx.strokeStyle = hc; ctx.lineWidth = 1; rr(lx - tw/2, ly - 11, tw, 22, 11); ctx.fill(); ctx.stroke();
    ctx.fillStyle = hc; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(label, lx, ly + .5);
    if (cur === N && N > 0) {
      ctx.strokeStyle = `rgba(147,212,139,${reduce ? .5 : .35 + .25*Math.sin(t/300)})`; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(head[0], head[1], 14, 0, 6.283); ctx.stroke();
    }
  }

  function setPlaying(on) {
    playing = on; const b = $('play');
    b.textContent = on ? '❚❚' : '▶'; b.title = on ? 'Pausar' : 'Animar';
    if (on && prog >= N) prog = 0;
  }
  function onStep(s) {
    lastStep = s; scrub.value = s;
    $('stepLbl').textContent = `Passo ${I[s].toLocaleString('pt-BR')} de ${totalSteps.toLocaleString('pt-BR')}`;
    $('op').innerHTML = OP[s];
  }

  let last = performance.now();
  function frame(t) {
    const dt = Math.min(64, t - last); last = t;
    if (playing && N > 0) { prog = Math.min(N, prog + dt / stepMs); if (prog >= N) setPlaying(false); }
    const s = Math.min(N, Math.floor(prog + 1e-6)); if (s !== lastStep) onStep(s);
    draw(t); requestAnimationFrame(frame);
  }

  $('play').onclick = () => setPlaying(!playing);
  $('restart').onclick = () => { prog = 0; setPlaying(true); };
  $('end').onclick = () => { setPlaying(false); prog = N; };
  scrub.oninput = () => { setPlaying(false); prog = +scrub.value; };
  cv.addEventListener('pointermove', (e) => {
    const rect = cv.getBoundingClientRect(), mx = e.clientX - rect.left;
    const target = ((mx - geo.m.l) / geo.iw) * totalSteps;
    let lo = 0, hi = N; while (lo < hi) { const mid = (lo + hi) >> 1; if (I[mid] < target) lo = mid + 1; else hi = mid; }
    const k = lo > 0 && Math.abs(I[lo - 1] - target) < Math.abs(I[lo] - target) ? lo - 1 : lo;
    if (mx < geo.m.l - 10 || k > Math.floor(prog + 1e-6)) { tip.hidden = true; return; }
    tip.textContent = `passo ${I[k].toLocaleString('pt-BR')}: ${strip(OP[k])}`; tip.hidden = false;
    tip.style.left = Math.min(Math.max(geo.P[k][0], 150), rect.width - 150) + 'px'; tip.style.top = geo.P[k][1] + 'px';
  });
  cv.addEventListener('pointerleave', () => tip.hidden = true);
  new ResizeObserver(() => layout()).observe(cv);

  setPlaying(playing); layout();
  requestAnimationFrame((t) => { last = t; frame(t); });
})();
</script>
"""


def marcas_lin(pico: int) -> list:
    """Linhas de altitude da escala linear, como [fração do pico, rótulo]."""
    lg = log10_int(pico)
    e = max(0, int(math.floor(lg - math.log10(4))))
    mant = 10 ** (lg - e)                       # pico ≈ mant · 10^e
    passo = next(s for s in (1, 2, 2.5, 5, 10, 20, 25, 50) if s >= mant / 4)
    marcas, k = [], passo
    while k <= mant:
        frac = k / mant
        valor = round(k * 10 ** e) if e < 15 else None
        marcas.append([frac, fmt(valor) if valor is not None else fmt_pot(k, e)])
        k += passo
    return marcas


def fmt_pot(k: float, e: int) -> str:
    while k >= 10:
        k /= 10
        e += 1
    return (f"{k:g}".replace(".", ",") + "·10" + str(e).translate(SUPER))


def marcas_log(pico: int) -> list:
    lg = log10_int(pico)
    if lg <= 0:
        return []
    bruto = max(1.0, lg / 6)
    mag = 10 ** math.floor(math.log10(bruto))
    passo = int(next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= bruto and float(s * mag).is_integer()))
    return [[p / lg, fmt(10 ** p) if p < 15 else "10" + str(p).translate(SUPER)]
            for p in range(0, int(lg) + 1, passo)]


lg_pico = log10_int(pico) or 1.0
dados = {
    "I": idx,
    "LIN": [round(seq[i] / pico, 6) for i in idx],
    "LG": [round(log10_int(seq[i]) / lg_pico, 6) for i in idx],
    "PAR": [paridade(seq[i]) for i in idx],
    "S": [fmt(seq[i]) for i in idx],
    "OP": [op_html(seq, i) for i in idx],
    "steps": passos,
    "peak": idx.index(pico_idx),
    "ms": ms,
    "scale": escala_js,
    "sampled": len(idx) < len(seq),
    "ticksLin": marcas_lin(pico),
    "ticksLog": marcas_log(pico),
}
components.html(CENA_HTML.replace("__DATA__", json.dumps(dados, ensure_ascii=False)), height=700)


# ============================================================
# Estatísticas
# ============================================================
st.markdown(f"""
<div class="stats">
  <div class="stat"><span class="lbl">Tempo de voo</span><span class="v">{fmt(passos)}</span><small>passos até o 1</small></div>
  <div class="stat"><span class="lbl">Altitude máxima</span><span class="v" style="color:{CORES['pico']}">{fmt(pico)}</span><small>no passo {fmt(pico_idx)} · {fmt(digitos(pico))} dígitos</small></div>
</div>
""", unsafe_allow_html=True)
st.caption(f"Ponto de partida com {fmt(digitos(n))} dígitos · trajetória calculada em {tempo_calc * 1000:,.0f} ms".replace(",", "."))


# ============================================================
# Diário da trilha
# ============================================================
st.markdown("### Diário da trilha")
st.markdown(f"""<div class="legenda">
<span><i style="background:{CORES['par']}"></i>par</span><span><i style="background:{CORES['impar']}"></i>ímpar</span>
<span><i style="background:{CORES['um']}"></i>chegada</span><span><i style="box-shadow:0 0 0 2px {CORES['pico']}"></i>pico</span></div>""",
            unsafe_allow_html=True)


def chip(i: int) -> str:
    v = seq[i]
    classe = "no pk" if i == pico_idx and passos > 0 else "no"
    cor = [CORES["par"], CORES["impar"], CORES["um"]][paridade(v)]
    return f'<span class="{classe}" style="color:{cor}" title="passo {i}: {op_curta(seq, i)}">{fmt(v)}</span>'


if len(seq) <= MAX_CHIPS:
    mostrar = list(range(len(seq)))
    pedacos = [chip(i) if k == 0 else '<span class="seta">→</span>' + chip(i) for k, i in enumerate(mostrar)]
else:
    metade = MAX_CHIPS // 2
    ini = [chip(i) for i in range(metade)]
    fim = [chip(i) for i in range(len(seq) - metade, len(seq))]
    sep = '<span class="seta">→</span>'
    pedacos = [sep.join(ini), f'<span class="corte">… {fmt(len(seq) - MAX_CHIPS)} passos omitidos …</span>', sep.join(fim)]
st.markdown(f'<div class="trilha">{"".join(pedacos)}</div>', unsafe_allow_html=True)
