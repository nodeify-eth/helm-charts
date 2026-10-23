# Contributing

Run the regression tests and lint every chart before submitting a change.
The Python and Helm versions used for validation are declared in the `env`
section of [.github/workflows/validate-charts.yaml](.github/workflows/validate-charts.yaml).
Install those versions locally; Python dependencies are pinned in
[requirements-dev.txt](requirements-dev.txt).
The regression tests also require Git, Helm, a POSIX `sh`, `jq`, and GNU
`sha256sum` on `PATH`. The Cosmos tests exercise the rendered download helper
with an offline fixture. CI installs Helm before running tests and checks that
the Ubuntu runner supplies `sh`, `jq`, and `sha256sum`.

From the repository root, create an isolated Python environment and run:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
for chart in charts/*/Chart.yaml; do
  helm lint "${chart%/Chart.yaml}" || exit 1
done
```

Keep the virtual environment out of your commits. The lint command checks all
six charts with their default values and needs no Kubernetes cluster.

The `Validate Charts` check runs these checks for every pull request, including
reopened pull requests and changes only to tests, workflows, or documentation.
It also runs on pushes to `main` and can be started manually from GitHub Actions.
Fork pull requests use read-only repository permissions and require no secrets.

Every change inside a surviving chart directory, including templates, values,
metadata, README files, and file deletions, requires a chart `version` strictly
greater than the current target branch version. Use a valid SemVer such as
`1.2.4` or `1.3.0-rc.1`; build metadata alone does not increase precedence.
New charts need a valid initial version. Entirely deleted charts and changes
outside chart directories do not require a bump.

Keep chart PRs up to date with the target branch by merging or rebasing it before
validation. To check a PR locally against the current target, run:

```sh
git fetch origin main
.venv/bin/python .github/scripts/check_chart_versions.py --base-ref origin/main --head-ref HEAD
```

The check reads committed content and reports the exact target and head commits.
Manually bump `version` and push the updated PR head when it fails, including on
forks. An `appVersion` update alone does not satisfy this policy. The existing
automatic appVersion bump may create a later commit; a successful check for an
earlier commit does not validate that new head. Pushes made with `GITHUB_TOKEN`
generally do not trigger another workflow run, so that head still needs validation.
Enforcing required checks and up-to-date branches in repository rules is an
owner configuration step beyond this local check.
