# Contributing

Run the regression tests and lint every chart before submitting a change.
The Python and Helm versions used for validation are declared in the `env`
section of [.github/workflows/validate-charts.yaml](.github/workflows/validate-charts.yaml).
Install those versions locally; Python dependencies are pinned in
[requirements-dev.txt](requirements-dev.txt).

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
