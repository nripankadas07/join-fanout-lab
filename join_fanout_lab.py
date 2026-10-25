"""Explain equi-join cardinality without materializing the multiplied join."""

import argparse
import html
import json
import sys
from pathlib import Path

import polars as pl


def analyze(data):
    if not isinstance(data, dict) or set(data) - {
        "left",
        "right",
        "keys",
        "how",
        "nulls_equal",
        "max_rows",
    }:
        raise ValueError(
            "expected left, right, keys and optional how/nulls_equal/max_rows"
        )
    keys = data.get("keys")
    if (
        not isinstance(keys, list)
        or not keys
        or len(keys) > 8
        or len(set(keys)) != len(keys)
        or not all(isinstance(k, str) and k for k in keys)
    ):
        raise ValueError("keys must be 1..8 distinct nonempty column names")
    how = data.get("how", "inner")
    if how not in {"inner", "left", "right", "full", "semi", "anti"}:
        raise ValueError("unsupported join strategy")
    nulls_equal = data.get("nulls_equal", False)
    cap = data.get("max_rows", 100000)
    if type(nulls_equal) is not bool or type(cap) is not int or not 0 <= cap <= 10**12:
        raise ValueError("nulls_equal must be boolean; max_rows integer 0..10^12")
    frames = []
    counts = []
    null_rows = []
    for side in ("left", "right"):
        rows = data.get(side)
        if not isinstance(rows, list) or len(rows) > 100000:
            raise ValueError(side + " must contain at most 100000 row objects")
        for row in rows:
            if not isinstance(row, dict) or any(k not in row for k in keys):
                raise ValueError(side + " rows must contain every join key")
            for k in keys:
                v = row[k]
                if v is not None and not (type(v) in (str, int, bool)):
                    raise ValueError(
                        "keys support text, integers, booleans and null only"
                    )
        # Explicitly reject implicit cross-type casting, including bool versus int.
        for k in keys:
            types = {type(row[k]) for row in rows if row[k] is not None}
            if len(types) > 1:
                raise ValueError("mixed key types in column " + k)
        selected = [{k: row[k] for k in keys} for row in rows]
        frame = (
            pl.DataFrame(selected, infer_schema_length=None)
            if rows
            else pl.DataFrame({k: [] for k in keys})
        )
        frames.append(frame)
        # Polars performs grouping on actual typed columns. Counts alone are joined below.
        grouped = (
            frame.group_by(keys).len()
            if rows
            else frame.with_columns(pl.lit(0).alias("len"))
        )
        counts.append(
            {tuple(row[k] for k in keys): row["len"] for row in grouped.to_dicts()}
        )
        null_rows.append(sum(any(row[k] is None for k in keys) for row in rows))
    for k in keys:
        ts = {
            type(row[k])
            for side in ("left", "right")
            for row in data[side]
            if row[k] is not None
        }
        if len(ts) > 1:
            raise ValueError("left/right key types differ in column " + k)
    left, right = counts
    contributions = []
    total = 0
    for key in set(left) | set(right):
        l, r = left.get(key, 0), right.get(key, 0)
        matchable = nulls_equal or all(v is not None for v in key)
        matched = l * r if matchable else 0
        if how == "inner":
            n = matched
        elif how == "left":
            n = matched if matched else l
        elif how == "right":
            n = matched if matched else r
        elif how == "full":
            n = matched if matched else l + r
        elif how == "semi":
            n = l if r and matchable else 0
        else:
            n = l if not r or not matchable else 0
        total += n
        contributions.append(
            {
                "key": list(key),
                "left_rows": l,
                "right_rows": r,
                "matched_pairs": matched,
                "output_rows": n,
                "many_to_many": bool(matchable and l > 1 and r > 1),
            }
        )
    contributions.sort(
        key=lambda x: (-x["output_rows"], json.dumps(x["key"], sort_keys=True))
    )
    match_keys = lambda c: [
        n for k, n in c.items() if nulls_equal or all(v is not None for v in k)
    ]
    l_unique = all(n <= 1 for n in match_keys(left))
    r_unique = all(n <= 1 for n in match_keys(right))
    return {
        "schema": "join-fanout/v1",
        "polars_version": pl.__version__,
        "how": how,
        "nulls_equal": nulls_equal,
        "left_rows": len(data["left"]),
        "right_rows": len(data["right"]),
        "output_rows": total,
        "max_rows": cap,
        "over_budget": total > cap,
        "null_key_rows": dict(zip(("left", "right"), null_rows)),
        "matching_key_cardinality": "1:1"
        if l_unique and r_unique
        else "1:m"
        if l_unique
        else "m:1"
        if r_unique
        else "m:m",
        "many_to_many_keys": sum(x["many_to_many"] for x in contributions),
        "key_count": len(contributions),
        "top_keys": contributions[:30],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input")
    p.add_argument("--html")
    args = p.parse_args(argv)
    try:
        result = analyze(load(args.input))
        if args.html:
            write_html(result, args.html)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if result["over_budget"] else 0
    except (ValueError, OSError, TypeError, pl.exceptions.PolarsError) as e:
        print(str(e), file=sys.stderr)
        return 2


def load(path):
    p = Path(path)
    if p.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("input exceeds 4 MiB")

    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError("duplicate JSON key: " + k)
            d[k] = v
        return d

    return json.loads(
        p.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite number")),
    )


def write_html(report, path):
    """Render escaped, searchable evidence tables without external assets."""
    esc = lambda x: html.escape(str(x))

    def table(headers, rows):
        return (
            "<table><thead><tr>"
            + "".join("<th>" + esc(x) + "</th>" for x in headers)
            + "</tr></thead><tbody>"
            + "".join(
                "<tr>" + "".join("<td>" + esc(x) + "</td>" for x in row) + "</tr>"
                for row in rows
            )
            + "</tbody></table>"
        )

    schema = report["schema"]
    sections = []
    cards = []
    if schema == "join-fanout/v1":
        title = "Where the extra join rows come from"
        subtitle = "Polars equi-join rehearsal. Group counts explain row growth before an expanded join is materialized."
        cards = [
            ("Left rows", report["left_rows"]),
            ("Right rows", report["right_rows"]),
            ("Output rows", report["output_rows"]),
            ("Row budget", report["max_rows"]),
        ]
        sections.append(
            "<h2>Keys contributing the most rows</h2>"
            + table(
                ["Key", "Left", "Right", "Matched pairs", "Output"],
                [
                    (
                        json.dumps(x["key"]),
                        x["left_rows"],
                        x["right_rows"],
                        x["matched_pairs"],
                        x["output_rows"],
                    )
                    for x in report["top_keys"]
                ],
            )
        )
        state = "Over row budget" if report["over_budget"] else "Within row budget"
    elif schema == "group-split-audit/v1":
        title = "Cross-validation split review"
        subtitle = "Review observable group, duplicate and time-window overlap before interpreting a validation score."
        cards = [
            ("Observations", report["rows"]),
            ("Folds", len(report["folds"])),
            ("Folds to review", sum(f["needs_review"] for f in report["folds"])),
        ]
        sections.append(
            "<h2>Fold findings</h2>"
            + table(
                [
                    "Fold",
                    "Train / test",
                    "Shared groups",
                    "Shared fingerprints",
                    "Window pairs",
                    "Unseen labels",
                ],
                [
                    (
                        f["fold"],
                        str(f["train_rows"]) + " / " + str(f["test_rows"]),
                        ", ".join(f["shared_groups"]) or "None",
                        ", ".join(f["shared_fingerprints"]) or "None",
                        f["overlapping_window_pairs"],
                        ", ".join(f["test_labels_absent_from_train"]) or "None",
                    )
                    for f in report["folds"]
                ],
            )
        )
        state = (
            "Review findings" if report["needs_review"] else "No declared overlap found"
        )
    elif schema == "compose-readiness-replay/v1":
        title = "What blocked startup"
        subtitle = "One ordered startup attempt, replayed against declared Compose dependency barriers."
        cards = [
            ("Events", len(report["timeline"])),
            ("Early starts", len(report["violations"])),
            ("Not started", len(report["not_started"])),
        ]
        sections.append(
            "<h2>Starts before their barriers were met</h2>"
            + table(
                ["Tick", "Service", "Waiting for"],
                [
                    (x["at"], x["service"], json.dumps(x["blocked_by"]))
                    for x in report["violations"]
                ],
            )
        )
        sections.append(
            "<h2>Observed event timeline</h2>"
            + table(
                ["Tick", "Service", "Event", "Ready to start after event"],
                [
                    (
                        x["at"],
                        x["service"],
                        x["event"],
                        ", ".join(x["ready_to_start"]) or "None",
                    )
                    for x in report["timeline"]
                ],
            )
        )
        state = (
            "Review findings"
            if report["needs_review"]
            else "Observed barriers respected"
        )
    elif schema == "n8n-relocation/v1":
        title = "Workflow relocation review"
        subtitle = "Local export reference mappings only. No server access, credential payloads or workflow activation."
        cards = [
            ("Planned mappings", len(report["operations"])),
            ("Unresolved references", len(report["unresolved"])),
        ]
        sections.append(
            "<h2>Reference changes</h2>"
            + table(
                ["Node", "Reference", "Before", "After"],
                [
                    (
                        x["node_id"],
                        x["kind"],
                        json.dumps(x["before"]),
                        json.dumps(x["after"]),
                    )
                    for x in report["operations"]
                ],
            )
        )
        sections.append(
            "<h2>Unresolved references</h2>"
            + table(
                ["Node", "Kind", "Reason"],
                [(x["node_id"], x["kind"], x["reason"]) for x in report["unresolved"]],
            )
        )
        state = (
            "Ready for review and local application"
            if report["ready"]
            else "Mapping is incomplete"
        )
    else:
        title = "Proxy wiring rehearsal"
        subtitle = "Local ASGI probes compare public redirects, documentation URLs and OpenAPI server prefixes."
        cards = [
            ("Scenarios", len(report["scenarios"])),
            ("Passing scenarios", sum(x["passed"] for x in report["scenarios"])),
        ]
        for scenario in report["scenarios"]:
            sections.append(
                "<h2>"
                + esc(scenario["name"])
                + (" · Pass" if scenario["passed"] else " · Review")
                + "</h2>"
                + table(
                    ["Public path", "Status", "Redirect / schema URL"],
                    [
                        (
                            x["path"],
                            x["status"],
                            x.get("location", x.get("docs_schema_url", "")),
                        )
                        for x in scenario["responses"]
                    ],
                )
            )
            sections.append(
                table(
                    ["Finding", "Path", "Evidence"],
                    [
                        (x["kind"], x["path"], json.dumps(x))
                        for x in scenario["findings"]
                    ],
                )
            )
        state = (
            "Review scenario differences"
            if report["needs_review"]
            else "All probe contracts passed"
        )
    body = html.escape(json.dumps(report, indent=2, ensure_ascii=False))
    css = "body{font:16px/1.6 system-ui;background:#f3f6fa;color:#182438;max-width:1100px;margin:40px auto;padding:0 24px}header{border-bottom:3px solid #137a68;padding-bottom:24px}h1{font-size:2.25rem;line-height:1.15;max-width:800px}h2{margin-top:40px;font-size:1.2rem}.cards{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.card{background:white;padding:16px 22px;border:1px solid #d2dae5;border-radius:10px;min-width:140px}.card b{display:block;font-size:1.7rem;color:#0b6555}table{border-collapse:collapse;width:100%;background:white;margin-bottom:22px;display:block;overflow:auto}th,td{text-align:left;padding:12px;border-bottom:1px solid #d6deea;vertical-align:top}th{background:#e3eaf2}td{overflow-wrap:anywhere}input{font:inherit;padding:10px;width:min(90%,600px);border:1px solid #8593a6;border-radius:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border:1px solid #d2dae5}.status{font-weight:700;color:#0b6555}footer{margin-top:40px;color:#4a5b73}details{margin-top:30px}label{display:block}"
    card_html = (
        '<div class="cards">'
        + "".join(
            '<div class="card">' + esc(k) + "<b>" + esc(v) + "</b></div>"
            for k, v in cards
        )
        + "</div>"
    )
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'
        + esc(title)
        + "</title><style>"
        + css
        + "</style><header><p>LOCAL DIAGNOSTICS · SYNTHETIC EXAMPLE WHEN USING THE BUNDLED FIXTURE</p><h1>"
        + esc(title)
        + "</h1><p>"
        + esc(subtitle)
        + '</p><p class="status">'
        + esc(state)
        + "</p></header>"
        + card_html
        + '<label>Filter evidence rows <input id="q" type="search" placeholder="Service, key, group, path or finding"></label>'
        + "".join(sections)
        + "<details><summary>Complete JSON evidence</summary><pre>"
        + body
        + '</pre></details><footer>Read the repository limitations before acting. These results describe supplied inputs; they do not certify a live system.</footer><script>document.querySelector("#q").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))});</script></html>'
    )
    Path(path).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
