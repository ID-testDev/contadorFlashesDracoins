# flash_fugaz.py
import streamlit as st
from collections import defaultdict, Counter
import unicodedata

try:
    import regex as re
    HAS_REGEX = True
except Exception:
    import re
    HAS_REGEX = False


st.set_page_config(page_title="Contador de Flash ID", layout="centered")

st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background-color: #3B82F6 !important;
    border-color: #3B82F6 !important;
    color: white !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #2563EB !important;
    border-color: #2563EB !important;
}
div.stButton > button[kind="primary"]:active {
    background-color: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
}
textarea:focus, input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 1px #3B82F6 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("💫 Contador de Flash ID")

with st.expander("📋 Ver formato de entrada", expanded=False):
    st.code(
"""> Definiciones A y B      <- título opcional (con o sin ">")

1. 🗺️🌹(🐼🍒)🌸🪼⚔️       <- primeros N = top, resto = otros
⚕️🧚🏻‍♀️🌙                  <- segunda línea (opcional): todos son "otros"
2. 🗺️⚔️🤸🏿‍♀️🪼🌙⚕️
🧚🏻‍♀️🎀🌸😾(🐼🍒)🌹
3. 🌙⚔️🐧🌹🪼(🐼🍒)         <- una sola línea: primeros N = top, resto = otros

- Paréntesis = ese conjunto es 1 solo participante
- Si hay segunda línea, toda ella cuenta como "otros"
- Si solo hay una línea, los primeros N son top y el resto otros
- N se configura en "Configuración de puntuación" (por defecto 6)""",
        language="text",
    )

st.divider()

# ── Constantes de output ────────────────────────────────────────────────────
HEADER      = "𓍯💫 ⊹ ࣪˖⁩ 𝕱𝖑𝖆𝖘𝖍 𝕱𝖚𝖌𝖆𝖟 ♡̷̷۫۫ ꕀ"
FOOTER      = "╰─ׄ     ︶⃨︶   : 🐐 :   ︶⃨︶     ─ׄ╯"
TOTAL_LABEL = "*`𝕋𝕆𝕋𝔸𝕃`*"
PART_PREFIX = "ꜜ ۪۪᭝໋݊"
PART_SUFFIX = "˒˒˒"

SUPERSCRIPTS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
}

INVISIBLE_CODEPOINTS = {
    0x2060, 0x200B, 0xFEFF, 0x200E, 0x200F,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
}


def to_superscript(n: int) -> str:
    return "".join(SUPERSCRIPTS.get(d, d) for d in str(n))


def normalize_participant(token):
    if not token:
        return token
    return "".join(ch for ch in token if ord(ch) not in INVISIBLE_CODEPOINTS)


def is_invisible_cluster(g):
    if not g:
        return True
    for ch in g:
        cat = unicodedata.category(ch)
        if cat.startswith(("L", "N", "S", "P")):
            return False
    return True


def graphemes(s):
    if not s:
        return []
    if HAS_REGEX:
        return re.findall(r"\X", s)
    return list(s)


def parse_participants_from_line(line):
    """Return ordered list of participant tokens from a line."""
    if not line:
        return []
    s = line.strip()
    # Strip leading round number like "1." or "1)"
    if re.match(r"^\s*\d+\s*[\.\-\)]\s*", s):
        _, s = s.split(".", 1)
        s = s.strip()
    # Strip leading "> "
    s = re.sub(r"^>\s*", "", s).strip()

    participants = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            j = s.find(")", i + 1)
            if j == -1:
                rest = s[i:].replace(" ", "")
                for g in graphemes(rest):
                    g = normalize_participant(g)
                    if g and not is_invisible_cluster(g):
                        participants.append(g)
                break
            inside = normalize_participant(s[i + 1:j].replace(" ", "").strip())
            if inside and not is_invisible_cluster(inside):
                participants.append(inside)
            i = j + 1
            continue
        if HAS_REGEX:
            m = re.match(r"\X", s[i:])
            g = normalize_participant(m.group(0))
            if g and not is_invisible_cluster(g):
                participants.append(g)
            i += len(m.group(0))
        else:
            cat = unicodedata.category(ch)
            if not ch.isspace() and not cat.startswith(("C", "Z")):
                ch_norm = normalize_participant(ch)
                if ch_norm:
                    participants.append(ch_norm)
            i += 1

    participants = [normalize_participant(p) for p in participants]
    return [p for p in participants if p and p != "."]


def is_round_start_line(line):
    return bool(re.match(r"^\s*\d+\s*[\.\-\)]\s*", line.strip()))


def parse_full_input(raw):
    raw = normalize_participant(raw or "")
    non_empty = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if not non_empty:
        return "", []

    titulo = ""
    start_idx = 0
    if not is_round_start_line(non_empty[0]):
        titulo = non_empty[0].lstrip(">").strip()
        start_idx = 1

    blocks = []
    current_block = None
    for line in non_empty[start_idx:]:
        if is_round_start_line(line):
            if current_block is not None:
                blocks.append(current_block)
            current_block = [line]
        else:
            if current_block is None:
                continue
            current_block.append(line)
    if current_block is not None:
        blocks.append(current_block)

    rondas = []
    for block in blocks:
        if not block:
            continue
        line1 = block[0]
        line2 = block[1] if len(block) > 1 else ""
        m_num = re.match(r"^\s*(\d+)\s*[\.\-\)]", line1)
        num = int(m_num.group(1)) if m_num else len(rondas) + 1
        rondas.append({"num": num, "line1": line1, "line2": line2})

    return titulo, rondas


def compute_round_scores(line1, line2, pts_top, pts_otros, n_top):
    all_line1 = parse_participants_from_line(line1)

    if line2:
        top_list = all_line1[:n_top]
        top_set = set(top_list)
        others_raw = parse_participants_from_line(line2)
        others = [p for p in others_raw if p not in top_set]
    else:
        top_list = all_line1[:n_top]
        top_set = set(top_list)
        others_raw = all_line1[n_top:]
        others = [p for p in others_raw if p not in top_set]

    scores = defaultdict(int)
    for p in top_list:
        scores[p] += pts_top
    for p in others:
        scores[p] += pts_otros

    return dict(scores), top_list, others, others_raw


def strip_round_number(line: str) -> str:
    return re.sub(r"^\s*\d+\s*[\.\-\)]\s*", "", line).strip()


def build_full_output(titulo, rondas, sorted_total):
    lines = [HEADER]
    if titulo:
        lines.append(f"> {titulo}")

    for ronda in rondas:
        sup = to_superscript(ronda["num"])
        stripped = strip_round_number(ronda["line1"])
        lines.append(f"⤿{sup}. {stripped}")
        if ronda["line2"]:
            lines.append(ronda["line2"])

    lines.append(TOTAL_LABEL)
    for p, pts in sorted_total:
        lines.append(f"{PART_PREFIX}{p}{PART_SUFFIX} {pts} - ")
    lines.append(FOOTER)

    return "\n".join(lines)


def copy_button_html(text, btn_id):
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    return f"""
    <button id="{btn_id}" onclick="
        navigator.clipboard.writeText(`{escaped}`)
          .then(() => {{ this.innerText='✅ Copiado!'; setTimeout(()=>this.innerText='📋 Copiar',2000); }})
          .catch(() => {{
            var ta=document.createElement('textarea'); ta.value=`{escaped}`;
            document.body.appendChild(ta); ta.select(); document.execCommand('copy');
            document.body.removeChild(ta);
            this.innerText='✅ Copiado!'; setTimeout(()=>this.innerText='📋 Copiar',2000);
          }});
    " style="background:#5865F2;color:white;border:none;padding:7px 16px;
             border-radius:6px;cursor:pointer;font-size:13px;margin-top:2px;">
    📋 Copiar</button>
    """


# ── Session state ───────────────────────────────────────────────────────────
if "analizado" not in st.session_state:
    st.session_state.analizado = False
if "raw_analizado" not in st.session_state:
    st.session_state.raw_analizado = ""

# ── Configuración de puntuación ─────────────────────────────────────────────
with st.expander("⚙️ Configuración de puntuación", expanded=False):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        n_top = st.number_input("Cantidad de TOP", min_value=1, max_value=20, value=6, step=1)
    with col_b:
        pts_top = st.number_input("Dcs para TOP", min_value=0, value=20, step=1)
    with col_c:
        pts_otros = st.number_input("Dcs para el resto", min_value=0, value=10, step=1)

st.divider()

# ── Input ───────────────────────────────────────────────────────────────────
raw_input = st.text_area(
    "Pega aquí el mensaje completo del flash",
    height=280,
    placeholder="> Definiciones A y B\n1. 🗺️🌹(🐼🍒)🌸🪼⚔️\n⚕️🧚🏻‍♀️🌙\n2. 🗺️⚔️🤸🏿‍♀️🪼🌙⚕️\n🧚🏻‍♀️🎀🌸😾(🐼🍒)🌹",
)

if raw_input != st.session_state.raw_analizado:
    st.session_state.analizado = False

if st.button("🔍 Analizar flash", type="primary", use_container_width=True):
    if not raw_input.strip():
        st.warning("Pega el mensaje del flash antes de analizar.")
        st.stop()
    st.session_state.analizado = True
    st.session_state.raw_analizado = raw_input

if not st.session_state.analizado:
    st.stop()

# ── Parse ───────────────────────────────────────────────────────────────────
titulo_detectado, rondas_detectadas = parse_full_input(st.session_state.raw_analizado)

st.divider()
st.markdown("### Vista previa")

col_n1, col_n2 = st.columns([1, 2])
with col_n1:
    st.markdown("**Título detectado:**")
with col_n2:
    titulo_final = st.text_input(
        "Título del flash",
        value=titulo_detectado,
        label_visibility="collapsed",
        placeholder="Sin título (opcional)",
    )

if not rondas_detectadas:
    st.warning("No se detectaron rondas. Verifica el formato.")
    st.stop()

# Advertir rondas no correlativas
nums = [r["num"] for r in rondas_detectadas]
expected = list(range(nums[0], nums[0] + len(nums)))
if nums != expected:
    faltantes = sorted(set(expected) - set(nums))
    st.warning(
        f"⚠️ Los números de ronda no son correlativos. Detectados: {nums}."
        + (f" Posibles faltantes: {faltantes}." if faltantes else "")
    )

st.markdown(f"**Rondas detectadas:** {len(rondas_detectadas)}")

for ronda in rondas_detectadas:
    r = ronda["num"]
    all_line1 = parse_participants_from_line(ronda["line1"])
    with st.expander(f"Ronda {r}", expanded=False):
        if ronda["line2"]:
            otros_prev = parse_participants_from_line(ronda["line2"])
            st.caption(f"Línea top: `{ronda['line1']}`")
            st.caption(f"Línea otros: `{ronda['line2']}`")
            st.caption(
                f"Top ({min(len(all_line1), n_top)}): "
                f"{' '.join(all_line1[:n_top]) or '(ninguno)'}"
            )
            st.caption(f"Otros: {' '.join(otros_prev) or '(ninguno)'}")
        else:
            st.caption(f"Línea única: `{ronda['line1']}`")
            st.caption(
                f"Top (primeros {n_top}): "
                f"{' '.join(all_line1[:n_top]) or '(ninguno)'}"
            )
            st.caption(f"Otros: {' '.join(all_line1[n_top:]) or '(ninguno)'}")

st.divider()

# ── Contar ──────────────────────────────────────────────────────────────────
if st.button("🧮 Contar flash", type="primary"):
    titulo_uso = titulo_final.strip()
    total_global = defaultdict(int)

    st.markdown("## Desglose por ronda")

    for ronda in rondas_detectadas:
        r = ronda["num"]
        line1, line2 = ronda["line1"], ronda["line2"]

        scores, top_list, others_list, others_raw = compute_round_scores(
            line1, line2, pts_top, pts_otros, n_top
        )

        # Más participantes de los esperados en la línea top (cuando hay segunda línea)
        all_line1 = parse_participants_from_line(line1)
        if len(all_line1) > n_top:
            st.warning(
                f"⚠️ Ronda {r}: Se detectaron **{len(all_line1)} participantes** en la línea "
                f"de top (se esperaban máximo {n_top}). Solo se tomaron los primeros {n_top}. "
                f"Revisa que la ronda esté bien formateada."
            )

        # Participante en top y en otros a la vez
        if line2:
            others_parsed = parse_participants_from_line(line2)
            ignored = [p for p in others_parsed if p in set(top_list)]
            if ignored:
                st.info(
                    f"Ronda {r}: {', '.join(ignored)} "
                    f"{'aparece' if len(ignored) == 1 else 'aparecen'} en top y en 'otros' "
                    f"— se contó solo el puntaje de top."
                )

        # Duplicados dentro del mismo grupo
        all_dups = [p for p, c in Counter(top_list + others_list).items() if c > 1]
        if all_dups:
            st.warning(f"Ronda {r}: Participantes repetidos: {', '.join(all_dups)}")

        for p, pts in scores.items():
            total_global[p] += pts

        sorted_round = sorted(scores.items(), key=lambda x: (-x[1], x[0]))

        with st.expander(f"Ronda {r}", expanded=False):
            if not sorted_round:
                st.info("Sin participantes detectados.")
            else:
                lines_out = "\n".join(f"{p}  {pts} Dcs" for p, pts in sorted_round)
                st.code(lines_out, language="text")

    # ── Output final ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## Output para publicar")

    sorted_total = sorted(total_global.items(), key=lambda x: (-x[1], x[0]))

    if not sorted_total:
        st.info("No se detectaron participantes en ninguna ronda.")
    else:
        full_output = build_full_output(titulo_uso, rondas_detectadas, sorted_total)
        st.code(full_output, language="text")
        st.components.v1.html(copy_button_html(full_output, "btn_output_final"), height=45)
