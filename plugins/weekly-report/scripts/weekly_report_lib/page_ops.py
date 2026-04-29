"""Surgical edits and template ops for weekly-report Confluence pages.

Page model: a 4-column table per user row.
  td[0] = name (contains <ri:user ri:account-id="..."/>)
  td[1] = 금주 진행
  td[2] = 차주 계획
  td[3] = 비고

Group label: 자동 생성 블록 식별자. 환경변수 WEEKLY_REPORT_GROUP_LABEL 로 override.
기본값은 'TEAM' — 이미 사용하던 Confluence 템플릿의 그룹 라벨로 설정 필요.
"""
from __future__ import annotations
import os
import re
from datetime import date, datetime, timedelta, timezone


def _row_spans(body: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    pos = 0
    while True:
        m = re.search(r"<tr\b", body[pos:])
        if not m:
            break
        start = pos + m.start()
        end_m = re.search(r"</tr>", body[start:])
        if not end_m:
            break
        end = start + end_m.end()
        spans.append((start, end))
        pos = end
    return spans


def find_user_row(body: str, account_id: str) -> tuple[int, int]:
    """Return (start, end) byte offsets of the unique <tr> containing account_id."""
    matches = [(s, e) for (s, e) in _row_spans(body) if account_id in body[s:e]]
    if len(matches) != 1:
        raise RuntimeError(f"expected 1 row for account-id={account_id}, found {len(matches)}")
    return matches[0]


def all_user_rows(body: str) -> list[tuple[str, tuple[int, int]]]:
    """Returns [(account_id, (row_start, row_end)), ...] for every user row."""
    rows: list[tuple[str, tuple[int, int]]] = []
    for s, e in _row_spans(body):
        m = re.search(r'ri:account-id="([^"]+)"', body[s:e])
        if m:
            rows.append((m.group(1), (s, e)))
    return rows


def split_row_cells(row: str) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    pos = 0
    while True:
        m = re.search(r"<td\b", row[pos:])
        if not m:
            break
        start = pos + m.start()
        end_m = re.search(r"</td>", row[start:])
        if not end_m:
            break
        end = start + end_m.end()
        cells.append((start, end))
        pos = end
    return cells


def replace_cell_inner(cell_xml: str, new_inner: str) -> str:
    m = re.match(r"(<td\b[^>]*>)(.*)(</td>)$", cell_xml, re.DOTALL)
    if not m:
        raise RuntimeError("malformed <td>")
    return m.group(1) + new_inner + m.group(3)


# ----- Auto-generated group block surgical splice.
# Confluence strips HTML comments, so we identify the auto-generated block by
# content: a <ul> whose first <li>'s first <p> contains the GROUP_LABEL text.
# Set WEEKLY_REPORT_GROUP_LABEL env var to your team's Confluence group label.

GROUP_LABEL = os.environ.get("WEEKLY_REPORT_GROUP_LABEL", "TEAM")
SDS_GROUP_LABEL = GROUP_LABEL  # backward-compat alias


def _find_matching_close(s: str, tag: str, start_after: int) -> int:
    """Find the offset of the matching </tag> for an open tag, handling nesting.
    `start_after` is the position right after the opening tag's '>'.
    Returns the offset of the '<' of the matching close tag, or -1 if not found.
    """
    depth = 1
    i = start_after
    open_re = re.compile(rf"<{tag}\b")
    close_str = f"</{tag}>"
    while i < len(s) and depth > 0:
        next_open = open_re.search(s, i)
        next_close = s.find(close_str, i)
        if next_close == -1:
            return -1
        if next_open and next_open.start() < next_close:
            depth += 1
            i = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return next_close
            i = next_close + len(close_str)
    return -1


def _find_sds_ul(inner: str) -> tuple[int, int] | None:
    """Find the (start, end) of a <ul>...</ul> whose first <li>'s first <p>
    contains the SDS_GROUP_LABEL text. End is exclusive (points past </ul>)."""
    pos = 0
    while True:
        m = re.search(r"<ul\b[^>]*>", inner[pos:])
        if not m:
            return None
        ul_open_start = pos + m.start()
        body_start = pos + m.end()
        close_lt = _find_matching_close(inner, "ul", body_start)
        if close_lt == -1:
            return None
        ul_end = close_lt + len("</ul>")
        ul_inner = inner[body_start:close_lt]
        # Inspect first <li>'s first <p>
        first_p = re.search(r"<li\b[^>]*>\s*<p\b[^>]*>([^<]*)</p>", ul_inner, re.DOTALL)
        if first_p and SDS_GROUP_LABEL in first_p.group(1):
            return (ul_open_start, ul_end)
        pos = ul_end


def _strip_all_sds_uls(cell_inner: str) -> str:
    """Remove every <ul>...</ul> whose first <li> first <p> contains GROUP_LABEL.
    Cleans up any duplicates left from prior runs."""
    while True:
        loc = _find_sds_ul(cell_inner)
        if not loc:
            return cell_inner
        s, e = loc
        cell_inner = cell_inner[:s] + cell_inner[e:]


def _splice_sds_block(cell_inner: str, new_sds_html: str) -> str:
    """Replace the existing group <ul> block (identified by content) with fresh HTML.
    Preserves all sibling content (other <ul> groups, free text, etc.). Removes
    duplicates if multiple group <ul>s exist (idempotent cleanup).

    new_sds_html is expected to be a <ul>...</ul> whose first item is GROUP_LABEL,
    or '<p />' when there are no items at all.
    """
    cell_inner = _strip_all_sds_uls(cell_inner)
    if new_sds_html.strip() in ("<p />", "<p/>", "<p></p>", ""):
        if cell_inner.strip() == "":
            return "<p />"
        return cell_inner
    if cell_inner.strip() in ("<p />", "<p/>", "<p></p>", ""):
        return new_sds_html
    return new_sds_html + cell_inner


def replace_user_cells(body: str, account_id: str, this_week_inner: str, next_week_inner: str) -> str:
    """Surgically refresh the user's auto-generated group block in 금주/차주 cells.

    The new content is wrapped in marker comments so future updates can find and
    replace just this block. Anything outside the markers (manual additions like
    'FE 파트', '회의' groups) is preserved across updates.
    """
    rs, re_ = find_user_row(body, account_id)
    row = body[rs:re_]
    cells = split_row_cells(row)
    if len(cells) < 4:
        raise RuntimeError(f"row has {len(cells)} cells, expected ≥4")
    new_row = row
    for idx, sds_html in [(2, next_week_inner), (1, this_week_inner)]:
        cs, ce = cells[idx]
        cell_xml = new_row[cs:ce]
        m = re.match(r"(<td\b[^>]*>)(.*)(</td>)$", cell_xml, re.DOTALL)
        if not m:
            raise RuntimeError("malformed <td>")
        open_tag, inner, close_tag = m.groups()
        spliced = _splice_sds_block(inner, sds_html)
        new_row = new_row[:cs] + open_tag + spliced + close_tag + new_row[ce:]
    return body[:rs] + new_row + body[re_:]


def clear_template(body: str) -> str:
    """Empty every user row's 금주/차주 cells. Used by create-next-week."""
    rows = all_user_rows(body)
    new_body = body
    for _account_id, (rs, re_) in reversed(rows):
        row = new_body[rs:re_]
        cells = split_row_cells(row)
        if len(cells) < 3:
            continue
        new_row = row
        for idx in (2, 1):
            cs, ce = cells[idx]
            new_row = new_row[:cs] + replace_cell_inner(new_row[cs:ce], "<p />") + new_row[ce:]
        new_body = new_body[:rs] + new_row + new_body[re_:]
    return new_body


def carry_template(body: str) -> str:
    """For Monday create: copy each user's 차주 계획 (cell 2) into 금주 진행 (cell 1),
    then clear 차주 계획. group blocks in cell 1 will be overwritten by update_all
    with fresh Jira data; manual sibling content (FE 파트 등) carries forward as
    'what we planned to do this week.' Cell 2 starts blank — update_all then puts
    fresh group items for this week's 차주 plan."""
    rows = all_user_rows(body)
    new_body = body
    for _account_id, (rs, re_) in reversed(rows):
        row = new_body[rs:re_]
        cells = split_row_cells(row)
        if len(cells) < 3:
            continue
        a2, b2 = cells[2]
        cell2_xml = row[a2:b2]
        m2 = re.match(r"(<td\b[^>]*>)(.*)(</td>)$", cell2_xml, re.DOTALL)
        cell2_inner = m2.group(2) if m2 else "<p />"
        new_row = row
        a, b = cells[2]
        new_row = new_row[:a] + replace_cell_inner(new_row[a:b], "<p />") + new_row[b:]
        a, b = cells[1]
        new_row = new_row[:a] + replace_cell_inner(new_row[a:b], cell2_inner) + new_row[b:]
        new_body = new_body[:rs] + new_row + new_body[re_:]
    return new_body


def _yymmdd(d: date) -> str:
    return f"{d.year % 100:02d}-{d.month:02d}-{d.day:02d}"


def update_header_dates(body: str, title: str) -> str:
    """Replace date ranges inside header <th> cells based on the title's Monday:
    - "금주 진행 (...)" → title_date ~ title_date + 4d (this week, Mon~Fri)
    - "차주 계획 (...)" → title_date + 7d ~ title_date + 11d (next week, Mon~Fri)
    Drops any annotation following the date range."""
    m = re.search(r"\((\d{2})-(\d{2})-(\d{2})\)", title)
    if not m:
        return body
    yy, mm, dd = (int(x) for x in m.groups())
    monday = date(2000 + yy, mm, dd)
    geumju = (monday, monday + timedelta(days=4))
    chaju = (monday + timedelta(days=7), monday + timedelta(days=11))

    def _repl(label: str, dates: tuple[date, date], src: str) -> str:
        new_range = f"({_yymmdd(dates[0])} ~ {_yymmdd(dates[1])})"

        def th_sub(m_th: re.Match[str]) -> str:
            inner = m_th.group(0)
            if label not in inner:
                return inner
            return re.sub(rf"({re.escape(label)}\s*)\([^)]*\)", rf"\1{new_range}", inner, count=1)

        return re.sub(r"<th\b[^>]*>.*?</th>", th_sub, src, flags=re.DOTALL)

    body = _repl("금주 진행", geumju, body)
    body = _repl("차주 계획", chaju, body)
    return body


# ----- Footer (auto-generation provenance) -----

FOOTER_START = "<!-- weekly-report-auto-footer-start -->"
FOOTER_END = "<!-- weekly-report-auto-footer-end -->"


def strip_footer(body: str) -> str:
    """Remove any prior auto-generated footer block (idempotent)."""
    s = body.find(FOOTER_START)
    e = body.find(FOOTER_END)
    if s == -1 or e == -1 or e < s:
        return body
    return body[:s] + body[e + len(FOOTER_END):]


def append_footer(body: str, *, source: str, generator: str, version: str, generated_at_kst: str) -> str:
    """Strip any existing auto-footer then append a fresh one."""
    base = strip_footer(body)
    footer = (
        f"{FOOTER_START}"
        f"<hr/>"
        f'<p><em>이 페이지는 sds-workflow 플러그인에 의해 자동 생성됨 — '
        f"v{version} · Source: {source} · Generator: {generator} · Generated at: {generated_at_kst}</em></p>"
        f"{FOOTER_END}"
    )
    return base + footer


# ----- Rendering -----

def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_grouped_list(groups: dict[str, list[str]], *, top_group: str | None = None) -> str:
    """Nested ul/li for {header: [items]}.

    If top_group is given (defaults to GROUP_LABEL), wraps the whole list under
    that top-level bullet — matching weekly-report templates where Jira items
    live under the team group and manual additions (e.g. side teams, meetings)
    go in separate top-level bullets.
    """
    if top_group is None:
        top_group = GROUP_LABEL
    if not groups:
        return "<p />"
    inner = "<ul>"
    for header, items in groups.items():
        if not items:
            continue
        inner += f"<li><p>{_escape(header)}</p>"
        inner += "<ul>" + "".join(f"<li><p>{_escape(i)}</p></li>" for i in items) + "</ul>"
        inner += "</li>"
    inner += "</ul>"
    if not top_group:
        return inner
    return f"<ul><li><p>{_escape(top_group)}</p>{inner}</li></ul>"


# ----- Title computation -----

def compute_next_title(prev_title: str, target_date: date | None = None) -> str:
    """Given '4월 5주차 주간 보고 (26-04-27)', compute next week's title."""
    m = re.search(r"\((\d{2})-(\d{2})-(\d{2})\)", prev_title)
    if not m:
        raise ValueError(f"cannot parse date from title: {prev_title!r}")
    yy, mm, dd = (int(x) for x in m.groups())
    if target_date is None:
        target_date = date(2000 + yy, mm, dd) + timedelta(days=7)
    week = _week_of_month(target_date)
    yy = target_date.year % 100
    return f"{target_date.month}월 {week}주차 주간 보고 ({yy:02d}-{target_date.month:02d}-{target_date.day:02d})"


def _week_of_month(d: date) -> int:
    first = d.replace(day=1)
    return ((d.day - 1 + first.weekday()) // 7) + 1


# ----- Folder hierarchy -----

def half_title(d: date) -> str:
    """e.g., 2026-04-27 → '2026년 주간보고 - 상반기' (no space between 주간 and 보고)."""
    return f"{d.year}년 주간보고 - {'상반기' if d.month <= 6 else '하반기'}"


def month_title(d: date) -> str:
    """e.g., 2026-05-04 → '5월 주간 보고' (with space between 주간 and 보고)."""
    return f"{d.month}월 주간 보고"


def kst_today_monday() -> date:
    """Monday of the current KST week (today if today is Monday)."""
    today = datetime.now(timezone(timedelta(hours=9))).date()
    return today - timedelta(days=today.weekday())


def find_child_by_title(children: list[dict], title: str) -> str | None:
    for c in children:
        if c.get("title") == title:
            return c["id"]
    return None


# ----- Categorization -----

def categorize(done: list[dict], active: list[dict]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    this_week = {"금주 완료": [f"{i['key']} {i['summary']}" for i in done]} if done else {}
    in_progress = [f"{i['key']} {i['summary']}" for i in active if i["status"] == "진행 중"]
    todo = [f"{i['key']} {i['summary']}" for i in active if i["status"] != "진행 중"]
    nw: dict[str, list[str]] = {}
    if in_progress:
        nw["진행 중 → 마무리"] = in_progress
    if todo:
        nw["신규 진행 예정"] = todo
    return this_week, nw
