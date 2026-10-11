
"""CourtVision: NBA player analytics with official NBA headshots."""

from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from main import (
    available_seasons,
    calculate_recent_form,
    calculate_scoring_consistency,
    calculate_stats,
    career_rows,
    create_database,
    find_player,
    generate_performance_insight,
    get_game_log,
    get_saved_players,
    get_saved_season_stats,
    get_shots,
    save_player,
    save_season_stats,
)

st.set_page_config(
    page_title="CourtVision | NBA Analytics",
    page_icon="🏀",
    layout="wide",
)

css_file = Path(__file__).with_name("styles.css")

if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

create_database()

ORANGE = "#f4511e"
BLUE = "#2455d6"
PAPER = "#f4f0e9"


# --------------------------------------------------
# NBA DATA AND CACHING
# --------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def career(player_id):
    return career_rows(player_id)


@st.cache_data(ttl=3600, show_spinner=False)
def games_for(player_id, season):
    return get_game_log(player_id, season)


@st.cache_data(ttl=3600, show_spinner=False)
def shots_for(player_id, season):
    return get_shots(player_id, season)


def headshot_url(player_id):
    """Official NBA headshot, not an AI-generated image."""
    return (
        "https://cdn.nba.com/headshots/nba/latest/"
        f"1040x760/{int(player_id)}.png"
    )


def show_headshot(player):
    """
    IMPORTANT: Render using Streamlit's actual image widget.

    Do not build an HTML <img> tag or convert
    the image to a Markdown string.
    """
    try:
        st.image(
            headshot_url(player["id"]),
            width="stretch",
        )
    except Exception:
        st.caption(
            "The official NBA headshot is unavailable "
            "for this player."
        )


def markup(source):
    """
    Small HTML fragments for typography and stat cards.
    Player photographs are NEVER rendered here.
    """
    cleaned = " ".join(
        line.strip() for line in source.splitlines()
    )

    st.markdown(
        cleaned,
        unsafe_allow_html=True,
    )


def h(value):
    return escape(str(value), quote=True)


def save_selection(player, stats):
    save_player(
        player["id"],
        player["full_name"],
    )

    save_season_stats(
        player["id"],
        stats,
    )


# --------------------------------------------------
# SHARED UI
# --------------------------------------------------

def heading(title):
    markup(
        f'<h2 class="cv-section">{h(title)}</h2>'
    )


def metric_card(label, value):
    markup(
        f'<div class="cv-metric">'
        f'<strong>{h(value)}</strong>'
        f'<span>{h(label)}</span>'
        f'</div>'
    )


def styled_figure(size=(5, 4)):
    fig, ax = plt.subplots(figsize=size)

    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    return fig, ax


def display_figure(fig):
    st.pyplot(fig, width="stretch")
    plt.close(fig)


# --------------------------------------------------
# PLAYER ANALYSIS CHARTS
# --------------------------------------------------

def draw_breakdown(stats):
    values = [
        max(0, stats[key])
        for key in ("two_pts", "three_pts", "ft_pts")
    ]

    total = sum(values)

    if not total:
        st.info("No scoring breakdown is available.")
        return

    fig, ax = styled_figure()

    ax.pie(
        values,
        colors=[
            ORANGE,
            "#5038c4",
            "#aaa0e2",
        ],
        startangle=90,
        counterclock=False,
        wedgeprops={
            "width": 0.28,
            "edgecolor": PAPER,
        },
    )

    ax.text(
        0,
        0.07,
        f'{stats["ppg"]}',
        ha="center",
        fontsize=27,
        fontweight="bold",
    )

    ax.text(
        0,
        -0.14,
        "PPG",
        ha="center",
        fontsize=11,
    )

    fig.tight_layout()
    display_figure(fig)

    labels = ("2PT", "3PT", "FT")

    summary = "  ·  ".join(
        f"{label}: {value / total:.0%}"
        for label, value in zip(labels, values)
    )

    st.caption(summary)


def draw_trend(games, ppg):
    recent = list(reversed(games[:10]))

    if not recent:
        st.info("No game logs available.")
        return

    x = np.arange(len(recent))

    points = [
        game["PTS"]
        for game in recent
    ]

    dates = [
        str(game["GAME_DATE"])
        for game in recent
    ]

    fig, ax = styled_figure()

    ax.plot(
        x,
        points,
        color=ORANGE,
        marker="o",
        linewidth=2.2,
        markersize=4,
    )

    ax.fill_between(
        x,
        points,
        color=ORANGE,
        alpha=0.12,
    )

    ax.axhline(
        ppg,
        color="#686868",
        linestyle="--",
        linewidth=1,
        label=f"Season: {ppg}",
    )

    ax.set_xticks(
        x,
        dates,
        rotation=45,
        ha="right",
        fontsize=7,
    )

    ax.grid(axis="y", alpha=0.16)
    ax.legend(frameon=False, fontsize=8)

    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    display_figure(fig)


def draw_shots(shots):
    points = [
        shot
        for shot in shots
        if shot.get("LOC_X") is not None
        and shot.get("LOC_Y") is not None
    ]

    if not points:
        st.info(
            "No shot-location data for this season."
        )
        return

    fig, ax = styled_figure()

    groups = (
        (0, "#b6ada4", "Missed"),
        (1, ORANGE, "Made"),
    )

    for flag, color, label in groups:
        subset = [
            shot
            for shot in points
            if shot.get("SHOT_MADE_FLAG") == flag
        ]

        ax.scatter(
            [s["LOC_X"] for s in subset],
            [s["LOC_Y"] for s in subset],
            color=color,
            s=9,
            alpha=0.48,
            label=label,
        )

    ax.set_xlim(-250, 250)
    ax.set_ylim(-55, 420)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.legend(
        frameon=False,
        fontsize=8,
    )

    fig.tight_layout()
    display_figure(fig)

    st.caption(
        "Real NBA shot locations · made and missed"
    )


def draw_recent(games):
    recent = list(reversed(games[:10]))

    if not recent:
        st.info("No recent games available.")
        return

    fig, ax = styled_figure()

    x = np.arange(len(recent))

    points = [
        game["PTS"]
        for game in recent
    ]

    bars = ax.bar(
        x,
        points,
        color=ORANGE,
    )

    ax.bar_label(
        bars,
        fontsize=8,
        padding=2,
    )

    ax.set_xticks(
        x,
        [
            str(game["GAME_DATE"])
            for game in recent
        ],
        rotation=45,
        ha="right",
        fontsize=7,
    )

    ax.grid(axis="y", alpha=0.16)
    ax.set_axisbelow(True)

    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    display_figure(fig)


# --------------------------------------------------
# PLAYER ANALYSIS DISPLAY
# --------------------------------------------------

def analysis_view(player, stats):

    # The player photograph is a real Streamlit
    # image widget, in its own layout column.

    with st.container(key="cv_analysis_hero"):
        col_text, col_photo = st.columns(
            [1.15, 1],
            vertical_alignment="center",
        )

        with col_text:
            st.caption(
                "PLAYER ANALYSIS / NBA DATA"
            )

            markup(
                '<h1 class="cv-player-title">'
                f'{h(player["full_name"])}'
                '</h1>'
            )

            markup(
                '<div class="cv-orange-rule"></div>'
            )

            markup(
                f'<div class="cv-team">'
                f'{h(stats["team"])}'
                '</div>'
            )

            st.caption(
                f'{stats["season"]} SEASON  /  '
                f'{stats["games"]} GAMES'
            )

            st.write(
                "Every season tells a story. "
                "Explore the numbers behind the game."
            )

        with col_photo:
            show_headshot(player)

    heading("THE NUMBERS DON'T LIE.")

    metrics = [
        ("PPG", stats["ppg"]),
        ("RPG", stats["rpg"]),
        ("APG", stats["apg"]),
        ("SPG", stats["spg"]),
        ("FG%", f'{stats["fg_pct"]}%'),
        ("TS%", f'{stats["ts_pct"]}%'),
    ]

    columns = st.columns(6, gap="small")

    for col, (label, value) in zip(
        columns,
        metrics,
    ):
        with col:
            metric_card(label, value)

    try:
        game_log = games_for(
            player["id"],
            stats["season"],
        )

    except Exception as error:
        st.warning(
            "Season averages loaded, but "
            "game-by-game analysis is unavailable: "
            f"{error}"
        )
        return

    # Equal-width visual sections
    columns = st.columns(3, gap="large")

    with columns[0]:
        heading("SCORING BREAKDOWN")
        draw_breakdown(stats)

    with columns[1]:
        heading("SCORING TREND")
        draw_trend(
            game_log,
            stats["ppg"],
        )

    with columns[2]:
        heading("SHOT DISTRIBUTION")

        try:
            shots = shots_for(
                player["id"],
                stats["season"],
            )

            draw_shots(shots)

        except Exception:
            st.info(
                "Shot-location data is unavailable "
                "for this season."
            )

    columns = st.columns(3, gap="large")

    with columns[0]:
        heading("SHOOTING EFFICIENCY")

        efficiency_stats = [
            ("FIELD GOAL %", "fg_pct"),
            ("TRUE SHOOTING %", "ts_pct"),
        ]

        for label, key in efficiency_stats:
            markup(
                '<div class="cv-eff-title">'
                f'{label}'
                f'<b>{stats[key]}%</b>'
                '</div>'
            )

            st.progress(
                min(
                    100,
                    max(0, int(stats[key])),
                )
            )

    with columns[1]:
        heading("RECENT PERFORMANCE")
        draw_recent(game_log)

    with columns[2]:
        heading("KEY INSIGHTS")

        recent = calculate_recent_form(game_log)

        markup(
            '<div class="cv-insight">'
            'SCORING FORM'
            '</div>'
        )

        st.write(
            generate_performance_insight(
                stats,
                recent,
            )
        )

        markup(
            '<div class="cv-insight">'
            'SCORING CONSISTENCY'
            '</div>'
        )

        consistency = calculate_scoring_consistency(
            game_log
        )

        if consistency is not None:
            st.write(
                f"{consistency:.2f} points "
                "standard deviation over up to "
                "10 recent games."
            )

        else:
            st.write(
                "Not enough games to measure "
                "scoring consistency."
            )

        markup(
            '<div class="cv-insight">'
            'SEASON SAMPLE'
            '</div>'
        )

        st.write(
            f'{stats["games"]} games '
            "in the season averages."
        )


# --------------------------------------------------
# COMPARISON TABLE
# --------------------------------------------------

def compare_metric_row(
    label,
    first,
    second,
    percent=False,
    lower_better=False,
):
    """
    Build a comparison row.

    The leader text uses a small badge,
    not the large stat font.
    """

    if lower_better:
        if first < second:
            winner = 1
        elif second < first:
            winner = 2
        else:
            winner = 0

    else:
        if first > second:
            winner = 1
        elif second > first:
            winner = 2
        else:
            winner = 0

    difference = abs(first - second)
    suffix = "%" if percent else ""

    if lower_better:
        lead_text = "STEADIER"
    else:
        lead_text = f"LEADS +{difference:.1f}"

    left_badge = ""
    right_badge = ""

    if winner == 1:
        left_badge = (
            '<span class="cv-leader orange">'
            f'{lead_text}'
            '</span>'
        )

    elif winner == 2:
        right_badge = (
            '<span class="cv-leader blue">'
            f'{lead_text}'
            '</span>'
        )

    return (
        '<div class="cv-compare-row">'
        '<div class="cv-compare-value">'
        f'{first:.1f}{suffix}'
        f'{left_badge}'
        '</div>'
        '<div class="cv-compare-label">'
        f'{h(label)}'
        '</div>'
        '<div class="cv-compare-value">'
        f'{second:.1f}{suffix}'
        f'{right_badge}'
        '</div>'
        '</div>'
    )


# --------------------------------------------------
# PLAYER COMPARISON DISPLAY
# --------------------------------------------------

def comparison_view(p1, p2, s1, s2):
    try:
        games1 = games_for(
            p1["id"],
            s1["season"],
        )

        games2 = games_for(
            p2["id"],
            s2["season"],
        )

    except Exception:
        games1 = []
        games2 = []

    # Require 10 games for a fair comparison.
    sd1 = (
        calculate_scoring_consistency(games1)
        if len(games1) >= 10
        else None
    )

    sd2 = (
        calculate_scoring_consistency(games2)
        if len(games2) >= 10
        else None
    )

    with st.container(key="cv_comparison_hero"):
        st.caption(
            "NBA ANALYTICS / HEAD TO HEAD"
        )

        last1 = h(
            p1["full_name"].split()[-1]
        )

        last2 = h(
            p2["full_name"].split()[-1]
        )

        markup(
            '<h1 class="cv-match-title">'
            f'{last1} <em>VS</em> {last2}'
            '</h1>'
        )

        st.caption(
            "TWO DIFFERENT GAMES. ONE COURT. "
            "REAL NBA DATA."
        )

        # Official photos on opposite sides,
        # comparison statistics in the center.
        col_left, col_middle, col_right = st.columns(
            [1, 1.45, 1],
            gap="small",
            vertical_alignment="center",
        )

        with col_left:
            show_headshot(p1)

            markup(
                '<div class="cv-nameplate orange">'
                f'{h(p1["full_name"])}'
                '<small>'
                f'{h(s1["team"])} · '
                f'{h(s1["season"])}'
                '</small>'
                '</div>'
            )

        with col_middle:
            table = (
                '<div class="cv-compare-table">'
                '<div class="cv-compare-header">'
                f'<span>{h(p1["full_name"])}</span>'
                '<span>STAT</span>'
                f'<span>{h(p2["full_name"])}</span>'
                '</div>'
            )

            rows = [
                ("POINTS PER GAME", "ppg", False),
                ("REBOUNDS PER GAME", "rpg", False),
                ("ASSISTS PER GAME", "apg", False),
                ("FIELD GOAL %", "fg_pct", True),
                ("TRUE SHOOTING %", "ts_pct", True),
            ]

            for label, key, is_percent in rows:
                table += compare_metric_row(
                    label,
                    s1[key],
                    s2[key],
                    percent=is_percent,
                )

            if sd1 is not None and sd2 is not None:
                table += compare_metric_row(
                    "SCORING SD · LOWER IS STEADIER",
                    sd1,
                    sd2,
                    lower_better=True,
                )

            else:
                table += (
                    '<p class="cv-compare-unavailable">'
                    '10 games per player needed for '
                    'consistency comparison.'
                    '</p>'
                )

            table += '</div>'

            markup(table)

        with col_right:
            show_headshot(p2)

            markup(
                '<div class="cv-nameplate blue">'
                f'{h(p2["full_name"])}'
                '<small>'
                f'{h(s2["team"])} · '
                f'{h(s2["season"])}'
                '</small>'
                '</div>'
            )

    # Head-to-head charts
    left, right = st.columns(
        2,
        gap="large",
    )

    with left:
        heading("PER-GAME PRODUCTION")

        fig, ax = styled_figure((6.5, 4))

        x = np.arange(3)
        width = 0.34

        values1 = [
            s1[key]
            for key in ("ppg", "rpg", "apg")
        ]

        values2 = [
            s2[key]
            for key in ("ppg", "rpg", "apg")
        ]

        bars1 = ax.bar(
            x - width / 2,
            values1,
            width,
            color=ORANGE,
            label=p1["full_name"],
        )

        bars2 = ax.bar(
            x + width / 2,
            values2,
            width,
            color=BLUE,
            label=p2["full_name"],
        )

        ax.bar_label(
            bars1,
            fmt="%.1f",
            padding=2,
            fontsize=9,
        )

        ax.bar_label(
            bars2,
            fmt="%.1f",
            padding=2,
            fontsize=9,
        )

        ax.set_xticks(
            x,
            ["POINTS", "REBOUNDS", "ASSISTS"],
        )

        ax.legend(
            frameon=False,
            fontsize=8,
        )

        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)

        ax.spines[["top", "right"]].set_visible(False)

        fig.tight_layout()
        display_figure(fig)

    with right:
        heading("TRUE SHOOTING COMPARISON")

        fig, ax = styled_figure((6.5, 4))

        bars = ax.bar(
            [0, 1],
            [
                s1["ts_pct"],
                s2["ts_pct"],
            ],
            color=[ORANGE, BLUE],
            width=0.55,
        )

        ax.bar_label(
            bars,
            labels=[
                f'{s1["ts_pct"]}%',
                f'{s2["ts_pct"]}%',
            ],
            padding=3,
            fontsize=11,
        )

        ax.set_xticks(
            [0, 1],
            [
                p1["full_name"].split()[-1],
                p2["full_name"].split()[-1],
            ],
        )

        ax.set_ylim(0, 100)
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)

        ax.spines[["top", "right"]].set_visible(False)

        fig.tight_layout()
        display_figure(fig)


# --------------------------------------------------
# WEBSITE HEADER AND TABS
# --------------------------------------------------

markup(
    '<div class="cv-brand">'
    '🏀 COURT<span>VISION</span>'
    '<small>'
    'BASKETBALL INTELLIGENCE / BUILT FOR THE GAME'
    '</small>'
    '</div>'
)

analysis_tab, compare_tab, saved_tab = st.tabs(
    [
        "PLAYER ANALYSIS",
        "COMPARE",
        "SAVED PLAYERS",
    ]
)


# --------------------------------------------------
# PLAYER ANALYSIS TAB
# --------------------------------------------------

with analysis_tab:

    with st.form("cv_analysis_form"):
        name = st.text_input(
            "Find an NBA player",
            placeholder=(
                "Search Kobe Bryant, Luka Doncic, "
                "Shai Gilgeous-Alexander..."
            ),
        )

        submitted = st.form_submit_button(
            "SEARCH"
        )

    if submitted:

        if not name.strip():
            st.warning("Enter a player name.")

            st.session_state.pop(
                "cv_player",
                None,
            )

        else:
            result = find_player(
                name.strip()
            )

            if result is None:
                st.warning(
                    "Player not found. "
                    "Check the spelling."
                )

                st.session_state.pop(
                    "cv_player",
                    None,
                )

            else:
                st.session_state["cv_player"] = result

    player = st.session_state.get(
        "cv_player"
    )

    if player:

        try:
            seasons = available_seasons(
                career(player["id"])
            )

            if not seasons:
                st.warning(
                    "No NBA seasons available."
                )

            else:
                selected = st.selectbox(
                    "SELECT SEASON",
                    seasons,
                    key=f"cv_season_{player['id']}",
                )

                stats = calculate_stats(
                    career(player["id"]),
                    selected,
                )

                save_selection(
                    player,
                    stats,
                )

                analysis_view(
                    player,
                    stats,
                )

        except Exception as error:
            st.error(
                "Couldn't load player analysis: "
                f"{error}"
            )


# --------------------------------------------------
# COMPARE TAB
# --------------------------------------------------

with compare_tab:

    with st.form("cv_compare_form"):

        left, right = st.columns(2)

        with left:
            name1 = st.text_input(
                "PLAYER ONE",
                placeholder="Luka Doncic",
            )

        with right:
            name2 = st.text_input(
                "PLAYER TWO",
                placeholder="Shai Gilgeous-Alexander",
            )

        submitted = st.form_submit_button(
            "COMPARE PLAYERS"
        )

    if submitted:

        if not name1.strip() or not name2.strip():
            st.warning(
                "Enter both player names."
            )

            st.session_state.pop(
                "cv_pair",
                None,
            )

        else:
            p1 = find_player(name1.strip())
            p2 = find_player(name2.strip())

            if p1 is None or p2 is None:
                st.warning(
                    "One or both players were not found."
                )

                st.session_state.pop(
                    "cv_pair",
                    None,
                )

            elif p1["id"] == p2["id"]:
                st.warning(
                    "Choose two different players."
                )

                st.session_state.pop(
                    "cv_pair",
                    None,
                )

            else:
                st.session_state["cv_pair"] = (
                    p1,
                    p2,
                )

    pair = st.session_state.get(
        "cv_pair"
    )

    if pair:
        p1, p2 = pair

        try:
            rows1 = career(p1["id"])
            rows2 = career(p2["id"])

            seasons1 = available_seasons(rows1)
            seasons2 = available_seasons(rows2)

            if not seasons1 or not seasons2:
                st.warning(
                    "Season data unavailable "
                    "for one player."
                )

            else:
                common = sorted(
                    set(seasons1) & set(seasons2),
                    reverse=True,
                )

                default1 = (
                    seasons1.index(common[0])
                    if common
                    else 0
                )

                default2 = (
                    seasons2.index(common[0])
                    if common
                    else 0
                )

                col1, col2 = st.columns(2)

                with col1:
                    season1 = st.selectbox(
                        f"{p1['full_name']} season",
                        seasons1,
                        index=default1,
                        key=f"cv_compare_left_{p1['id']}",
                    )

                with col2:
                    season2 = st.selectbox(
                        f"{p2['full_name']} season",
                        seasons2,
                        index=default2,
                        key=f"cv_compare_right_{p2['id']}",
                    )

                stats1 = calculate_stats(
                    rows1,
                    season1,
                )

                stats2 = calculate_stats(
                    rows2,
                    season2,
                )

                save_selection(p1, stats1)
                save_selection(p2, stats2)

                if season1 != season2:
                    st.caption(
                        "Different seasons are selected; "
                        "compare with that context in mind."
                    )

                comparison_view(
                    p1,
                    p2,
                    stats1,
                    stats2,
                )

        except Exception as error:
            st.error(
                "Couldn't load comparison: "
                f"{error}"
            )


# --------------------------------------------------
# SAVED PLAYERS TAB
# --------------------------------------------------

with saved_tab:

    heading("SAVED PLAYERS")

    stored_players = get_saved_players()

    if stored_players:
        df_players = pd.DataFrame(
            stored_players,
            columns=[
                "Player ID",
                "Player",
            ],
        )

        st.dataframe(
            df_players,
            hide_index=True,
            width="stretch",
        )

    else:
        st.info(
            "Search for a player to add them "
            "to your library."
        )

    stored_stats = get_saved_season_stats()

    if stored_stats:
        heading(
            "SAVED SEASON STATISTICS"
        )

        df_stats = pd.DataFrame(
            stored_stats,
            columns=[
                "Player ID",
                "Season",
                "Team",
                "Games",
                "PPG",
                "RPG",
                "APG",
                "SPG",
                "FG%",
                "TS%",
            ],
        )

        st.dataframe(
            df_stats,
            hide_index=True,
            width="stretch",
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

markup(
    '<footer class="cv-footer">'
    'COURTVISION / INDEPENDENT NBA ANALYTICS PROJECT'
    ' · NBA DATA & HEADSHOTS VIA NBA SERVICES'
    '</footer>'
)
