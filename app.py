"""Interface graphique Streamlit - Quiz chronométré multijoueur.

Réutilise les classes POO de quiz.py (Question, QuestionBank, Player,
Joker, Leaderboard...). Lancer avec :  streamlit run app.py
"""
from __future__ import annotations

import html
import math
import re
import time

import streamlit as st

from quiz import BASE_DIR, LETTERS, Leaderboard, Player, QuestionBank, QuestionContext

BASE_POINTS = 10
MAX_TIME_BONUS = 10
MEDALS = ["🥇", "🥈", "🥉", "🎖️"]

st.set_page_config(page_title="Quiz chronométré", page_icon="🎯", layout="centered")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp, .stApp p, .stApp button, .stApp label, .stApp input, .stApp h1, .stApp h2, .stApp h3,
.stApp [data-testid="stMarkdownContainer"] {font-family:'Inter','Segoe UI',system-ui,sans-serif;}
.block-container {max-width: 680px; padding-top: 4rem;}
[data-testid="stToolbar"], [data-testid="stDecoration"] {display:none;}
[data-testid="stHeader"] {background:transparent;}

/* ---- carte du quiz (fond gris très clair, coins arrondis) ---- */
.st-key-card {background:#f4f5f9; border:1px solid #e1e4ec; border-radius:16px;
              padding:18px 20px 26px; gap:0 !important;}
.st-key-card [data-testid="stHorizontalBlock"] {gap:8px !important; margin-top:12px;}

/* ---- barre du chrono ---- */
.timer-wrap {display:flex; align-items:center; gap:14px; margin:0; padding-bottom:16px;}
.timer-track {flex:1; height:9px; background:#e2e5ec; border-radius:99px; overflow:hidden;}
.timer-fill {height:100%; background:#f5a524; border-radius:99px; transition: width 1s linear;}
.timer-fill.low {background:#e5484d;}
.timer-label {font-weight:700; font-size:.78rem; color:#2b2f3a; min-width:26px; text-align:right;}

/* ---- boîte de la question (bleu nuit, texte blanc gras centré) ---- */
.q-box {background:#16264b; border-radius:10px; padding:26px 20px; text-align:center; margin:0 0 20px;}
.q-box span {display:block; max-width:17em; margin:0 auto; color:#fff; font-weight:700;
             font-size:1.02rem; line-height:1.75;}

/* ---- infos / scores ---- */
.meta {font-size:.88rem; color:#6b7280; margin: 2px 0 8px;}
.chips {display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;}
.chip {display:flex; gap:10px; align-items:center; background:#f3f4f6; color:#111827;
       border:2px solid transparent; border-radius:999px; padding:5px 14px; font-size:.88rem;}
.chip.active {background:#fff7e6; border-color:#f5a524;}

/* ---- choix : bouton blanc, lettre violette à gauche, texte centré ---- */
[class*="st-key-choice_"] button {
  position:relative; min-height:56px; border-radius:8px; border:1.5px solid #cdd2dd;
  background:#ffffff !important; color:#2b2f3a !important; padding:0 44px; box-shadow:none;
  transition: border-color .15s, background .15s;
}
[class*="st-key-choice_"] button p {margin:0; font-size:.95rem; font-weight:500; text-align:center; color:inherit;}
[class*="st-key-choice_"] button::before {
  position:absolute; left:18px; top:50%; transform:translateY(-50%);
  font-weight:800; font-size:.85rem; color:#5b4bd5;
}
[class*="st-key-choice_0_"] button::before {content:"A";}
[class*="st-key-choice_1_"] button::before {content:"B";}
[class*="st-key-choice_2_"] button::before {content:"C";}
[class*="st-key-choice_3_"] button::before {content:"D";}
[class*="st-key-choice_"] button:hover:not(:disabled) {border-color:#5b4bd5; background:#f7f6ff !important;}
[class*="st-key-choice_"] button:disabled {opacity:.85;}
[class*="st-key-choice_"][class*="_correct"] button {
  background:#2e7d32 !important; border-color:#2e7d32 !important; color:#ffffff !important; opacity:1 !important;}
[class*="st-key-choice_"][class*="_wrong"] button {
  background:#c62828 !important; border-color:#c62828 !important; color:#ffffff !important; opacity:1 !important;}
[class*="st-key-choice_"][class*="_correct"] button::before,
[class*="st-key-choice_"][class*="_wrong"] button::before {color:#ffffff;}
[class*="st-key-choice_"][class*="_hidden"] button {opacity:.3;}

.podium {display:flex; justify-content:space-between; align-items:center; padding:12px 18px;
         border-radius:12px; margin-bottom:8px; background:#f3f4f6; color:#111827; font-size:1.1rem;}
.podium.first {background:#fff7e6; border:2px solid #f5a524;}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
#  Utilitaires
# ----------------------------------------------------------------------
def md_escape(text: str) -> str:
    """Échappe la ponctuation pour que '__init__' ou '@x' s'affichent tels quels."""
    return re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", text)


def nbsp_punct(text: str) -> str:
    """Espace insécable avant ? ! : ; (évite un « ? » seul sur la dernière ligne)."""
    return re.sub(r" ([?!:;])", "\u00a0\\1", text)


def game() -> dict:
    return st.session_state.game


def current_player(g: dict) -> Player:
    return g["players"][g["idx"] % len(g["players"])]


# ----------------------------------------------------------------------
#  Logique du jeu (callbacks)
# ----------------------------------------------------------------------
def start_game(names: list[str], category: str, seconds: int, per_player: int) -> None:
    bank = QuestionBank(BASE_DIR / "questions.json")
    players = [Player(n) for n in names]
    questions = bank.draw(category, per_player * len(players))
    st.session_state.game = {
        "players": players, "questions": questions, "category": category,
        "seconds": seconds, "idx": 0, "ctx": QuestionContext(questions[0]),
        "deadline": time.time() + seconds, "result": None, "chosen": None,
        "points": 0, "frozen": float(seconds), "message": "",
        "recorded": False, "celebrated": False,
    }
    st.session_state.phase = "game"


def resolve(result: str, chosen: int | None = None) -> None:
    g = game()
    remaining = max(0.0, g["deadline"] - time.time())
    g.update(result=result, chosen=chosen, frozen=remaining, points=0)
    if result == "correct":
        bonus = int(MAX_TIME_BONUS * remaining / g["seconds"])
        g["points"] = BASE_POINTS + bonus
        current_player(g).add_points(g["points"])


def on_answer(i: int) -> None:
    g = game()
    if g["result"] is not None:
        return
    if time.time() >= g["deadline"]:
        resolve("timeout")
        return
    resolve("correct" if i == g["ctx"].question.answer else "wrong", i)


def on_joker(key: str) -> None:
    g = game()
    joker = current_player(g).jokers[key]
    if g["result"] is not None or joker.used:
        return
    joker.used = True
    g["message"] = joker.apply(g["ctx"])
    if g["ctx"].passed:
        resolve("pass")


def on_next() -> None:
    g = game()
    g["idx"] += 1
    if g["idx"] >= len(g["questions"]):
        if not g["recorded"]:
            Leaderboard(BASE_DIR / "leaderboard.json").record(g["players"])
            g["recorded"] = True
        st.session_state.phase = "results"
        return
    g.update(ctx=QuestionContext(g["questions"][g["idx"]]),
             deadline=time.time() + g["seconds"],
             result=None, chosen=None, points=0, message="")


def on_restart() -> None:
    st.session_state.pop("game", None)
    st.session_state.phase = "setup"


# ----------------------------------------------------------------------
#  Composants d'affichage
# ----------------------------------------------------------------------
def timer_bar(remaining: float, total: int) -> None:
    pct = max(0.0, min(100.0, remaining / total * 100))
    low = " low" if remaining <= 5 else ""
    st.markdown(
        f'<div class="timer-wrap"><div class="timer-track">'
        f'<div class="timer-fill{low}" style="width:{pct:.0f}%"></div></div>'
        f'<span class="timer-label">{math.ceil(remaining)} s</span></div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every=1)
def timer_fragment() -> None:
    """Se rafraîchit chaque seconde ; déclenche la fin de question à 0 s."""
    g = game()
    if g["result"] is not None:
        return
    remaining = g["deadline"] - time.time()
    if remaining <= 0:
        resolve("timeout")
        st.rerun()
    timer_bar(remaining, g["seconds"])


def scoreboard(g: dict) -> None:
    cur = g["idx"] % len(g["players"])
    chips = "".join(
        f'<div class="chip{" active" if i == cur else ""}">'
        f"<span>{html.escape(p.name)}</span><b>{p.score}</b></div>"
        for i, p in enumerate(g["players"])
    )
    st.markdown(f'<div class="chips">{chips}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
#  Écrans
# ----------------------------------------------------------------------
def setup_view() -> None:
    st.title("🎯 Quiz chronométré")
    st.caption("Multijoueur local · 2 à 4 joueurs · jokers · classement persistant")
    bank = QuestionBank(BASE_DIR / "questions.json")

    n = st.radio("Nombre de joueurs", [2, 3, 4], horizontal=True)
    with st.form("setup"):
        raw_names = [st.text_input(f"Joueur {i + 1}", value=f"Joueur{i + 1}", key=f"name_{i}")
                     for i in range(n)]
        category = st.selectbox("Catégorie", bank.categories)
        c1, c2 = st.columns(2)
        seconds = c1.slider("Temps par question (s)", 5, 30, 15)
        per_player = c2.slider("Questions par joueur", 1, 10, 5)
        submitted = st.form_submit_button("🚀 Commencer", type="primary", width="stretch")

    if submitted:
        names = [x.strip() or f"Joueur{i + 1}" for i, x in enumerate(raw_names)]
        if len({x.lower() for x in names}) < len(names):
            st.error("Chaque joueur doit avoir un nom différent.")
        else:
            start_game(names, category, seconds, per_player)
            st.rerun()

    with st.expander("🏆 Classement général"):
        leaderboard_table()


def leaderboard_table() -> None:
    data = Leaderboard(BASE_DIR / "leaderboard.json").data
    if not data:
        st.caption("Aucune partie jouée pour l'instant.")
        return
    rows = sorted(data.items(), key=lambda kv: kv[1]["total"], reverse=True)
    st.dataframe(
        [{"Joueur": k, "Points": v["total"], "Parties": v["games"], "Victoires": v["wins"]}
         for k, v in rows],
        hide_index=True, width="stretch",
    )


def game_view() -> None:
    g = game()
    ctx: QuestionContext = g["ctx"]
    q = ctx.question
    player = current_player(g)
    answered = g["result"] is not None

    scoreboard(g)
    st.markdown(
        f'<div class="meta">Question {g["idx"] + 1}/{len(g["questions"])} · '
        f"🎮 <b>{html.escape(player.name)}</b> · {html.escape(g['category'])}</div>",
        unsafe_allow_html=True,
    )

    with st.container(key="card"):
        if answered:
            timer_bar(g["frozen"], g["seconds"])
        else:
            timer_fragment()

        st.markdown(f'<div class="q-box"><span>{html.escape(nbsp_punct(q.text))}</span></div>',
                    unsafe_allow_html=True)

        # --- les 4 choix en grille 2x2 ---
        for row in range(0, len(q.choices), 2):
            cols = st.columns(2, gap="small")
            for i in (row, row + 1):
                if i >= len(q.choices):
                    continue
                if i in ctx.hidden:
                    state = "hidden"
                elif answered and i == q.answer:
                    state = "correct"
                elif answered and i == g["chosen"]:
                    state = "wrong"
                else:
                    state = "idle"
                label = "—" if state == "hidden" else md_escape(q.choices[i])
                with cols[i % 2]:
                    with st.container(key=f"choice_{i}_{state}"):
                        st.button(label, key=f"ans_{g['idx']}_{i}", on_click=on_answer, args=(i,),
                                  disabled=answered or state == "hidden", width="stretch")

    # --- jokers ---
    st.write("")
    jcols = st.columns(3)
    jcols[0].markdown('<div class="meta" style="padding-top:.55rem">Jokers disponibles</div>', unsafe_allow_html=True)
    icons = {"J": "✂️", "P": "⏭️"}
    for col, key in zip(jcols[1:], ("J", "P")):
        joker = player.jokers[key]
        col.button(f"{icons[key]} {joker.label}", key=f"joker_{key}_{g['idx']}",
                   on_click=on_joker, args=(key,), disabled=answered or joker.used,
                   width="stretch")

    # --- retour d'information ---
    if not answered and g["message"]:
        st.info(f"✨ {g['message']}")
    if answered:
        res = g["result"]
        good = f"{LETTERS[q.answer]}. {md_escape(q.choices[q.answer])}"
        if res == "correct":
            st.success(f"✅ Bonne réponse ! **+{g['points']} points**")
        elif res == "wrong":
            st.error(f"❌ Faux. La bonne réponse était : {good}")
        elif res == "timeout":
            st.warning(f"⌛ Temps écoulé ! La bonne réponse était : {good}")
        else:
            st.info("⏭️ Question passée (0 point).")
        last = g["idx"] + 1 >= len(g["questions"])
        st.button("🏁 Voir les résultats" if last else "Question suivante →",
                  type="primary", on_click=on_next, width="stretch")


def results_view() -> None:
    g = game()
    st.title("🏁 Résultats")
    ranked = sorted(g["players"], key=lambda p: p.score, reverse=True)
    for i, p in enumerate(ranked):
        first = " first" if p.score == ranked[0].score else ""
        st.markdown(
            f'<div class="podium{first}"><span>{MEDALS[min(i, 3)]} {html.escape(p.name)}</span>'
            f"<b>{p.score} pts</b></div>",
            unsafe_allow_html=True,
        )
    if not g["celebrated"]:
        st.balloons()
        g["celebrated"] = True

    st.subheader("🏆 Classement général")
    leaderboard_table()
    st.button("🔁 Rejouer", type="primary", on_click=on_restart, width="stretch")


# ----------------------------------------------------------------------
#  Routage
# ----------------------------------------------------------------------
st.session_state.setdefault("phase", "setup")
{"setup": setup_view, "game": game_view, "results": results_view}[st.session_state.phase]()