# Research and alternatives

Observed on 25 October 2026; repository metadata snapshot at 06:05 UTC, with narrower
comparison searches and README reads later in the same review. Exact receipts
are retained in the portfolio ledger. Searches request GitHub star ordering;
topic/keyword coverage is limited and does not establish a global ranking.

Queries: `topic:dataframe stars:>10000 archived:false sort:stars; polars join audit sort:stars`.

| Repository | Observed stars | Last push observed UTC | API license classification |
| --- | ---: | --- | --- |
| [pandas-dev/pandas](https://github.com/pandas-dev/pandas) | 50268 | 2026-10-25T04:25:56Z | BSD-3-Clause |
| [pola-rs/polars](https://github.com/pola-rs/polars) | 40187 | 2026-10-25T05:45:20Z | MIT |
| [unionai-oss/pandera](https://github.com/unionai-oss/pandera) | 4497 | 2026-10-25T02:30:14Z | MIT |

The highest-star relevant comparable found among these is recorded in the table.
Stars indicate an audience to investigate, not user demand or technical quality.
NOASSERTION/unclassified licenses require separate review before reusing code.
These comparables were read as evidence; no competitor code/prose was reused.

## User and evidence

Data engineers joining stock, order or event tables in Polars. A duplicated business key can multiply a join result. A row-count surprise is easier to investigate before the expanded table exists.

- https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.join.html
- https://github.com/pola-rs/polars/issues/20947

Inferred demand for this report. The current Polars documentation already supports join validation and explicit null matching. The streaming tracking issue supplies engine context, not a request for this tool and not proof of a current join bug.

## Workflow comparison

Polars executes joins; pandas also provides merge validation; Pandera validates data contracts. This tool adds a bounded preflight row budget and per-key contribution evidence without materializing the multiplied result. No claim that those projects cannot produce similar diagnostics with additional code.

Our first useful result is the bundled install-and-report example. The other
projects have their own setup, examples and support channels; their installation
times were not benchmarked here. No speed, memory, reliability or feature-absence
superiority claim follows from our successful example. Their broader workflows
may be more appropriate for larger or different tasks.

## Scope and portfolio comparison

Existing table-reconcile compares keyed CSV versions with decimal tolerances; sql-null-witness explains predicates. Neither is being republished here. This tool examines join multiplicity and validates its counts against Polars itself.

The five selected projects address separate tasks: join cardinality, fold leakage,
ASGI URL wiring, container startup history and workflow export relocation. They
are not forks or subdivisions of one application. A portfolio-wide inventory of
218 repositories was compared before selection. Reusable packaging/report
boilerplate does not count as the original capability.

One pinned Polars dependency plus its platform runtime wheel. Recheck null semantics and the join oracle before upgrading. It is not a general data-quality platform.

Discovery path: Searchable Polars many-to-many join and null-matching examples, a row-growth HTML report and an entry in the portfolio index.

Candidate rank 1 of 5 reflects practical usefulness, problem evidence,
distinctness, demonstrability and maintenance burden. It is a judgment, not a
measured score or a prediction of attention. Playwright/browser-agent ideas were
set aside because the existing portfolio already has tracing/replay tools.
Generic top-star lists/tutorial collections were not selected as product anchors.
Polars is used for a Polars-native workflow even though pandas has more stars;
scikit-learn fits the selected evaluation task rather than larger general ML repos.
