# Join Fanout Lab

A duplicated business key can multiply a join result. A row-count surprise is easier to investigate before the expanded table exists.

Compute exact equi-join output counts from grouped keys, show the largest contributors and flag a chosen row budget.

## Try the example

Python 3.11+ on Linux. No account or remote service is needed.

```sh
git clone https://github.com/nripankadas07/join-fanout-lab.git
cd join-fanout-lab
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade "pip>=26.2" "setuptools>=84.1"
python -m pip install .
join-fanout-lab example.json --html report.html
```

The invented stock example predicts 8 left-join rows from 4 left rows and 5 right rows. Key [P17, A] contributes 6 rows, exceeding the configured total budget of 6.

The JSON goes to stdout; open `report.html` in a browser for searchable evidence
tables. The bundled [HTML report](demo.html) and [expected JSON](example-output.json)
come from [example.json](example.json), which uses invented data.

Exit 0 means a completed report without the tool's documented review findings;
exit 1 means findings require review; exit 2 means invalid input or an operational
error, with stderr and no partial JSON report. Some bundled examples intentionally
exit 1 to demonstrate a failure diagnosis. Do not discard those findings.


## Input and supported behavior

`left` and `right` are arrays of row objects. `keys` names 1..8 common columns. `how` is inner/left/right/full/semi/anti; default inner. `nulls_equal` defaults false. `max_rows` defaults 100000. Non-key values are ignored.

## Limits and compatibility

Up to 100000 rows per side and 4 MiB JSON. Key values are text, integers, booleans or null, with one non-null type per column across both sides. No floats, expressions, coercion, as-of/inequality/cross joins, lazy scans or memory/latency estimates. Counts use full inputs, not sampling. The report includes at most 30 key groups and can expose business identifiers.

Polars 2.0.0, installed from the official Python package registry

One pinned Polars dependency plus its platform runtime wheel. Recheck null semantics and the join oracle before upgrading. It is not a general data-quality platform.

## Verify

```sh
python -m unittest -v
python -m compileall -q .
python -m pip wheel --no-deps -w dist .
python -m venv /tmp/join-fanout-lab-check
/tmp/join-fanout-lab-check/bin/python -m pip install dist/*.whl
/tmp/join-fanout-lab-check/bin/python verify_installed.py
```

The installed check executes the real console command from a temporary working
directory and checks malformed-input exit behavior. CI repeats tests and clean
installation on Python 3.11/3.13, then runs a vulnerability audit. See
[validation coverage](VALIDATION.md) for tested behavior and remaining limits.

## Why this project

Existing table-reconcile compares keyed CSV versions with decimal tolerances; sql-null-witness explains predicates. Neither is being republished here. This tool examines join multiplicity and validates its counts against Polars itself.

Polars executes joins; pandas also provides merge validation; Pandera validates data contracts. This tool adds a bounded preflight row budget and per-key contribution evidence without materializing the multiplied result. No claim that those projects cannot produce similar diagnostics with additional code.

[Research and alternatives](RESEARCH.md) records dated sources, stars, licenses,
maintenance observations and demand limits. No adoption or performance advantage
is claimed. Original code and invented fixtures, developed with AI assistance.
No affiliation with or endorsement by the upstream project is implied.

[License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Brief](BRIEF.json)
