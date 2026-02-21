# Pearl Certification — neighborhood placement

Home buyers moving to Charlottesville are placed into neighborhoods by how well their energy (E), water
(W) and resilience (R) goals match each neighborhood's certification scores, subject to each buyer's own
ranking of the neighborhoods and an even split of buyers per neighborhood. Text in, text out, standard
library only. The constraint is the interesting part: once everyone is housed, no buyer may be able to
move somewhere they prefer *and* outfit someone already living there — the stable-matching condition,
which this program guarantees and can re-check.

## A whole run

```
$ head -5 input.txt
N N0 E:7 W:7 R:10
N N1 E:2 W:1 R:1
N N2 E:7 W:6 R:4
H H0 E:3 W:9 R:2 N2>N0>N1
H H1 E:4 W:3 R:7 N0>N2>N1

$ python main.py --verify
verified: stable placement of 12 buyers across 3 neighborhoods
wrote generated_output.txt

$ cat generated_output.txt
N0: H5(161) H11(154) H2(128) H4(122)
N1: H9(23) H8(21) H7(20) H1(18)
N2: H6(128) H3(120) H10(86) H0(83)
```

Twelve buyers, three neighborhoods, four slots each. **H0** got its first choice, N2, scoring
`3·7 + 9·6 + 2·4 = 83` — the weakest fit there, kept only because no better-fitting buyer who preferred N2
was still looking. **H1** also led with N0 but scores 119 there, below all four who stayed, so it was
rejected; it tried N2 (74, again below all four) and ended in N1, its last choice, at 18. One rejection
cascades into the next, and that cascade is the whole algorithm.

That transcript, plus a second input with named neighborhoods and an uneven split (thirteen buyers over
four neighborhoods, capacities 4/3/3/3), is in [docs/example-run.txt](docs/example-run.txt).

## Running it

Python 3.10 or newer, nothing to install.

```bash
git clone <repository-url> pearl-certification-assessment
cd pearl-certification-assessment
python main.py                     # input.txt -> generated_output.txt
python main.py --stdout --verify   # print, re-checking stability first
```

Every option is a flag (`--help` lists all five) — no env vars, no config file, so a run is fully
described by the command that produced it. Exit codes: `0` fine, `1` the result failed `--verify`, `2`
unreadable or unparseable input, with parse errors naming the line and quoting it (`line 1: expected 5
fields, got 4 in 'N N0 E:1 W:1'`). `--scorer` picks the fit function: only `dot`, the one the brief
defines, is registered, but `scoring.py` keeps a `Scorer` protocol and a registry so an alternative costs
no change to the matching code. Input is one record per line, `#` comments skipped, integers only, names
unique:

```
N <name> E:<int> W:<int> R:<int>
H <name> E:<int> W:<int> R:<int> <pref>><pref>><pref>
```

## Why Gale–Shapley, and what it replaced

Neighborhoods are hospitals, an even share of buyers is capacity, fit score is how a neighborhood ranks
buyers — so this is hospitals/residents, and buyer-proposing Gale-Shapley solves it exactly: it
terminates, it places every buyer who ranks every neighborhood, and of all stable assignments it returns
the one best for the buyers.

Before that, `assign` was a single greedy sweep — visit each neighborhood once, take the buyers who ranked
it first, rehome the overflow. With no way to revisit a neighborhood already decided, a buyer displaced
late can never compete for one settled early; the H1 cascade above is exactly what it cannot do. Over 60
generated inputs at three neighborhoods and twelve buyers it left a blocking pair on 18, and at five and
twenty on 53 of 60 — while being correct on the one input the brief ships, which is why the suite
generates inputs instead of a golden file. Its failing shapes are pinned as `REGRESSION` in
`tests/test_matching.py`.

The rule itself is checked, not assumed: `find_blocking_pair` restates it as code and knows nothing about
Gale-Shapley, walking each buyer's preferences above their current placement for a free slot or a resident
they outfit. Tests assert against *that* rather than expected output; `--verify` runs it.

## Tests

296 tests, most of them one property repeated: 84 inputs generated from seven neighborhood/buyer shapes ×
twelve seeds, each checked three ways — stable, every buyer placed once, every capacity exact. The rest
cover parsing, rendering, the scorer registry, CLI exit codes, the five regression shapes, and the golden
answer for the shipped input. `pip install -r requirements-dev.txt`, then `python -m pytest`
([296 passed in 0.15s](docs/test-run.txt)) and `ruff check .`; `python scripts/benchmark.py` produces the
table below.

## Where the time goes

Ranking buyers within each neighborhood is `O(M·N log N)` and dominates the `O(N·M)` proposals, each a
dict lookup into a fit matrix built once up front. Python 3.14.5, Apple Silicon
([docs/benchmark.txt](docs/benchmark.txt)):

| neighborhoods | buyers | parse | assign | verify |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 12 | 0.000s | 0.000s | 0.000s |
| 10 | 1,000 | 0.003s | 0.009s | 0.008s |
| 25 | 10,000 | 0.046s | 0.255s | 0.238s |
| 50 | 50,000 | 0.352s | 3.943s | 3.586s |

The last two columns owe their shape to measuring: the stability check first rescanned the assignment per
buyer, which made it quadratic and dominant past ten thousand buyers, and each neighborhood now holds its
residents in a rank-keyed heap, so a displacement costs `O(log capacity)` rather than a scan.

## What is not here

- **No UI, API, database or persistence.** The brief asked for a program that reads a file and writes a
  file; the evidence is captured terminal output under `docs/`, nothing to screenshot.
- **Docker is written but never built.** `Dockerfile`, `docker-compose.yml` and `.dockerignore` are
  present and `docker compose config` parses, but no image has been built or booted here — reviewed
  source, not a verified artifact.
- **A partial preference list can leave a buyer unplaced** rather than forced somewhere they did not rank;
  the output is simply shorter. (Capacity remainders go to the earliest neighborhoods, so an inexact split
  never drops anyone.)
- **Ties break by buyer name:** arbitrary but deterministic, where a real product would want a defensible
  rule.
- **Single process, in memory, integer scores only** — the parser rejects decimals, per the format.
