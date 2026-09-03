"""Generate the phone-first Ops Money-Printer dashboard (self-contained
HTML) from the live ops_digest roster. Static output — no drift from data.

Usage: python3 scripts/build_digest_artifact.py <out.html>
"""
import html
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")
from foundation.ops_digest import (  # noqa: E402
    live_opportunities, STATUS_ORDER, RULED_OUT, ruled_out_count)

STATUS_META = {
    "ACTIONABLE_NOW": ("DO NOW", "go"),
    "ACT_SOON": ("ACT SOON", "soon"),
    "PURSUE": ("PURSUE", "pursue"),
    "UNVERIFIED": ("UNVERIFIED", "unver"),
    "WATCH": ("WATCH", "watch"),
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def card(o, i, total, now) -> str:
    if o.is_expired(now):
        d = o.deadline_date()
        label, cls = f"CLOSED {d.isoformat() if d else ''}".strip(), "watch"
        steps = (f'      <li>This closed on {d.isoformat() if d else "the stated date"}'
                 " — here for the record, not to act on.</li>")
    else:
        label, cls = STATUS_META[o.status]
        steps = "\n".join(f"      <li>{esc(a)}</li>" for a in o.actions)
    note = (f'\n    <p class="note">⚠️ {esc(o.note)}</p>' if o.note else "")
    return f"""  <article class="card {cls}" id="{esc(o.opp_id)}">
    <div class="stripe"></div>
    <div class="body">
      <div class="cardhead">
        <span class="badge {cls}">{esc(label)}</span>
        <span class="idx">{i}/{total}</span>
      </div>
      <h2>{esc(o.title)}</h2>
      <p class="what">{esc(o.what)}</p>
      <div class="value">{esc(o.value)}</div>
      <div class="chips">
        <span class="chip"><span class="k">GATE</span> {esc(o.gate)}</span>
        <span class="chip deadline"><span class="k">DEADLINE</span> {esc(o.deadline)}</span>
      </div>
      <div class="dothis">DO THIS</div>
      <ol>
{steps}
      </ol>{note}
      <a class="go" href="{esc(o.link)}" target="_blank" rel="noopener">Open →</a>
      <div class="src">{esc(o.source_ref)}</div>
    </div>
  </article>"""


def main(out_path: str) -> None:
    now = datetime.now(timezone.utc)
    opps = live_opportunities(now)
    total = len(opps)
    counts = {}
    for o in opps:
        counts[o.effective_status(now)] = counts.get(o.effective_status(now), 0) + 1
    pills = "\n".join(
        f'      <span class="pill {STATUS_META[s][1]}">{counts[s]} '
        f'{esc(STATUS_META[s][0])}</span>'
        for s in STATUS_ORDER if counts.get(s))
    live_count = sum(1 for o in opps if not o.is_expired(now))
    cards = "\n".join(card(o, i, total, now) for i, o in enumerate(opps, 1))
    ruled_rows = "\n".join(
        f'    <li><b>{esc(r.title)}</b> <span class="rv">{esc(r.value)}</span>'
        f'<br><span class="rw">{esc(r.wall)}</span></li>'
        for r in RULED_OUT)
    ruled_html = (
        '  <details class="ruledout"><summary>❌ Ruled out '
        f'({ruled_out_count()}) — shown so you can challenge them</summary>\n'
        '    <p class="rhint">Each was eliminated on a quoted clause. If a wall '
        'has changed (new insurance, a partner\'s turnover, a consortium), it '
        'moves back into play — that\'s why they\'re here, not hidden.</p>\n'
        f'    <ul>\n{ruled_rows}\n    </ul>\n  </details>')
    doc = f"""<title>Ops Money-Printer</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#f4f6fb; --surface:#ffffff; --surface2:#eef1f7; --ink:#141925;
  --muted:#5a6478; --line:#dde2ec;
  --go:#1a7f37; --soon:#9a6700; --pursue:#1f5fd0; --unver:#8a6d0c; --watch:#5a6478;
  --go-bg:#e7f6ec; --soon-bg:#fbf3df; --pursue-bg:#e6eefc; --unver-bg:#f8f2d8; --watch-bg:#eceef3;
  --accent:#1a7f37;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0c0f16; --surface:#141925; --surface2:#1b2130; --ink:#e6ebf5;
    --muted:#8b95ab; --line:#242c3d;
    --go:#3fb950; --soon:#d29922; --pursue:#4c8dff; --unver:#d4a72c; --watch:#8b95ab;
    --go-bg:#0f2417; --soon-bg:#2a2110; --pursue-bg:#0f1f3d; --unver-bg:#2a2410; --watch-bg:#1b2130;
    --accent:#3fb950;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0c0f16; --surface:#141925; --surface2:#1b2130; --ink:#e6ebf5;
  --muted:#8b95ab; --line:#242c3d;
  --go:#3fb950; --soon:#d29922; --pursue:#4c8dff; --unver:#d4a72c; --watch:#8b95ab;
  --go-bg:#0f2417; --soon-bg:#2a2110; --pursue-bg:#0f1f3d; --unver-bg:#2a2410; --watch-bg:#1b2130;
  --accent:#3fb950;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans", system-ui, sans-serif; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:680px; margin:0 auto; padding:0 16px 64px; }}
header {{
  position:sticky; top:0; z-index:10; background:var(--bg);
  border-bottom:1px solid var(--line); padding:18px 16px 14px;
  margin:0 -16px 20px;
}}
header .inner {{ max-width:680px; margin:0 auto; }}
h1 {{ font-size:1.35rem; margin:0 0 2px; letter-spacing:-.01em; }}
h1 .coin {{ filter:saturate(1.2); }}
.stamp {{ font-family:"IBM Plex Mono", monospace; font-size:.72rem; color:var(--muted); }}
.lead {{ font-size:.9rem; color:var(--muted); margin:8px 0 12px; }}
.pills {{ display:flex; flex-wrap:wrap; gap:6px; }}
.pill {{ font-family:"IBM Plex Mono", monospace; font-size:.68rem; font-weight:600;
  padding:4px 9px; border-radius:999px; white-space:nowrap; }}
.pill.go{{background:var(--go-bg);color:var(--go);}}
.pill.soon{{background:var(--soon-bg);color:var(--soon);}}
.pill.pursue{{background:var(--pursue-bg);color:var(--pursue);}}
.pill.unver{{background:var(--unver-bg);color:var(--unver);}}
.pill.watch{{background:var(--watch-bg);color:var(--watch);}}
.card {{ display:flex; background:var(--surface); border:1px solid var(--line);
  border-radius:14px; overflow:hidden; margin:0 0 14px; }}
.stripe {{ width:5px; flex:0 0 5px; }}
.card.go .stripe{{background:var(--go);}}
.card.soon .stripe{{background:var(--soon);}}
.card.pursue .stripe{{background:var(--pursue);}}
.card.unver .stripe{{background:var(--unver);}}
.card.watch .stripe{{background:var(--watch);}}
.body {{ padding:16px 16px 14px; flex:1; min-width:0; }}
.cardhead {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
.badge {{ font-family:"IBM Plex Mono", monospace; font-size:.66rem; font-weight:700;
  letter-spacing:.06em; padding:4px 9px; border-radius:6px; }}
.badge.go{{background:var(--go-bg);color:var(--go);}}
.badge.soon{{background:var(--soon-bg);color:var(--soon);}}
.badge.pursue{{background:var(--pursue-bg);color:var(--pursue);}}
.badge.unver{{background:var(--unver-bg);color:var(--unver);}}
.badge.watch{{background:var(--watch-bg);color:var(--watch);}}
.idx {{ font-family:"IBM Plex Mono", monospace; font-size:.7rem; color:var(--muted); }}
h2 {{ font-size:1.05rem; margin:0 0 6px; letter-spacing:-.01em; text-wrap:balance; }}
.what {{ font-size:.88rem; color:var(--muted); margin:0 0 12px; }}
.value {{ font-family:"IBM Plex Mono", monospace; font-weight:600; font-size:1.15rem;
  color:var(--go); margin:0 0 12px; word-break:break-word; }}
.card.soon .value{{color:var(--soon);}} .card.pursue .value{{color:var(--pursue);}}
.card.unver .value{{color:var(--unver);}} .card.watch .value{{color:var(--ink);}}
.chips {{ display:flex; flex-direction:column; gap:6px; margin:0 0 14px; }}
.chip {{ font-size:.8rem; background:var(--surface2); border:1px solid var(--line);
  border-radius:8px; padding:7px 10px; }}
.chip .k {{ font-family:"IBM Plex Mono", monospace; font-size:.62rem; font-weight:700;
  color:var(--muted); letter-spacing:.08em; margin-right:6px; }}
.chip.deadline .k {{ color:var(--soon); }}
.dothis {{ font-family:"IBM Plex Mono", monospace; font-size:.66rem; font-weight:700;
  letter-spacing:.1em; color:var(--muted); margin:0 0 6px; }}
ol {{ margin:0 0 12px; padding-left:20px; }}
ol li {{ font-size:.9rem; margin:0 0 6px; }}
.note {{ font-size:.82rem; background:var(--soon-bg); color:var(--soon);
  border-radius:8px; padding:9px 11px; margin:0 0 12px; }}
.go {{ display:block; text-align:center; background:var(--accent); color:#fff;
  font-weight:600; text-decoration:none; padding:12px; border-radius:10px;
  font-size:.95rem; }}
.go:active {{ opacity:.85; }}
.src {{ font-family:"IBM Plex Mono", monospace; font-size:.62rem; color:var(--muted);
  margin-top:10px; word-break:break-word; }}
footer {{ text-align:center; color:var(--muted); font-size:.72rem;
  font-family:"IBM Plex Mono", monospace; margin-top:24px; }}
.ruledout {{ background:var(--surface); border:1px solid var(--line);
  border-radius:14px; padding:14px 16px; margin:0 0 14px; }}
.ruledout summary {{ font-weight:600; cursor:pointer; color:var(--ink); }}
.ruledout .rhint {{ font-size:.82rem; color:var(--muted); margin:10px 0 12px; }}
.ruledout ul {{ list-style:none; padding:0; margin:0; }}
.ruledout li {{ font-size:.86rem; padding:10px 0; border-top:1px solid var(--line); }}
.ruledout .rv {{ font-family:"IBM Plex Mono", monospace; color:var(--muted);
  font-size:.78rem; margin-left:6px; }}
.ruledout .rw {{ color:var(--muted); }}
</style>

<header><div class="inner">
  <h1><span class="coin">💰</span> Ops Money-Printer</h1>
  <div class="stamp">{now.strftime('%a %d %b %Y · %H:%M UTC')}</div>
  <p class="lead">{live_count} live opportunities you can move on. {ruled_out_count()} ruled out (shown at the bottom, with the clause that ruled each out). Most-winnable first.</p>
  <div class="pills">
{pills}
  </div>
</div></header>

<div class="wrap">
{cards}
{ruled_html}
  <footer>TITANOS · generated from OPS_BOARD.md · figures traceable per card</footer>
</div>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"wrote {out_path} ({len(doc)} bytes, {total} cards)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ops_digest.html")
