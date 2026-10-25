# Validation coverage

Local Linux/Python 3.12 validation includes core unit/integration cases, real
ecosystem APIs where used, runnable invented example, wheel build and clean
installed console-command checks outside the source tree. The original failure
expectations are preserved while implementation defects are corrected.

## Acceptance checks

- All six supported join modes agree with actual Polars joins across 144 seeded composite-key/null cases.
- A 400-by-500 duplicated key reports 200000 output rows without creating the expanded join.
- Mixed key types, missing keys, duplicate JSON keys and nonfinite numbers reject.

CI must pass on the intended public default-branch commit before this project is
counted as a verified launch. Public repository existence alone is insufficient.
Remote CI links and commit receipts belong in the portfolio ledger; this text
does not claim an unobserved run passed.

Windows/macOS, production data and live external service operation are untested.
Up to 100000 rows per side and 4 MiB JSON. Key values are text, integers, booleans or null, with one non-null type per column across both sides. No floats, expressions, coercion, as-of/inequality/cross joins, lazy scans or memory/latency estimates. Counts use full inputs, not sampling. The report includes at most 30 key groups and can expose business identifiers.

The cloud browser rejects local file URLs, so the generated HTML report was
checked structurally and for escaped output but was not visually inspected in
that browser. Console behavior and installed commands are independently tested.

The initial new-project environment audit flagged its preinstalled pip 25.0.1.
The installer is upgraded to pip 26.2+ before dependency installation and the
full environment audit is rerun. Project runtime dependencies were not the
source of those installer advisories. No advisory is suppressed.
