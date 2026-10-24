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
python3.15 -m venv .venv
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
forks. An `appVersion` update alone does not satisfy this policy. The automatic
appVersion bump may create a later commit for same-repository PRs. Fork and
Dependabot PRs require manual version changes. Any author version change is
preserved; an invalid or insufficient change still fails the version check.
Prerelease or build-metadata versions require a manual version increase when
appVersion changes.

After a bot bump, confirm the actual final commit SHA on the PR. GitHub creates
approval-required PR workflow runs for `opened`, `synchronize`, and `reopened`
events caused by `GITHUB_TOKEN`; ordinary token-generated push runs remain
suppressed. A maintainer with write access must review the final commit and
workflow changes, then select **Approve workflows to run** on the PR. Verify that
`Validate Charts` runs on that exact final SHA and passes. A successful earlier
run does not validate the bot commit. See GitHub's
[workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

If no final-head run or approval banner appears, the branch author or maintainer
can fetch the PR source branch, confirm its current SHA, and request a fresh
human-triggered run with a content-identical empty commit:

```sh
git rev-parse HEAD
git commit --allow-empty -m "ci: request validation for current chart head"
git push
```

Run these commands only on the current PR source branch after fetching its latest
commits. This creates a new final head; verify that head's `Validate Charts` run
passes (approve it if required). The empty commit does not cause another version
bump. Rerunning the old pre-bump workflow retains its original SHA; the generic
manual workflow run also skips PR version checks. Neither substitutes for this
final-head validation. If the PR head or target advances during a run, update the
branch and validate its current head again.

Enforcing required checks and up-to-date branches in repository rules is an
owner configuration step beyond this local check.

## Chart documentation

Tier 2 documentation is generated with `helm-docs` **1.14.2**. Put that exact
version on `PATH`; the wrapper checks its version before rendering.

From the repository root, regenerate the README after reviewing changes to
`charts/substreams-tier-2/Chart.yaml`, `values.yaml`, or `README.md.gotmpl`:

```sh
.venv/bin/python .github/scripts/generate_chart_docs.py substreams-tier-2
.venv/bin/python .github/scripts/generate_chart_docs.py --check substreams-tier-2
```

The generator accepts the explicit chart name `substreams-tier-2`.
`--check` reports documentation drift without writing files. Edit the template
for prose changes and the values comments for configuration descriptions;
`README.md` is the rendered output. Apply the chart version policy above before
regenerating so its badge matches the final package version.

The wrapper regression tests use a fake executable in temporary repositories,
so running the ordinary Python test suite does not require `helm-docs`.
