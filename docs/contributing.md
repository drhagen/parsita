---
icon: material/hand-heart
---

# Contributing

Parsita is free and open source software developed under an MIT license. Development occurs at the [GitHub project](https://github.com/drhagen/parsita). Contributions, big and small, are welcome.

Bug reports and feature requests may be made directly on the [issues](https://github.com/drhagen/parsita/issues) tab.

To make a pull request, you will need to fork the repo, clone the repo, make the changes, run the tests, push the changes, and [open a PR](https://github.com/drhagen/parsita/pulls).

## Cloning the repo

To make a local copy of Parsita, clone the repository with git:

```shell
git clone https://github.com/drhagen/parsita.git
```

## Installing from source

Parsita uses uv as its packaging and dependency manager. In whatever Python environment you prefer, install uv and then use uv to install Parsita and its dependencies:

```shell
pip install uv
uv sync
```

## Testing

Parsita uses pytest to run the tests in the `tests/` directory. The test command is encapsulated with Nox:

```shell
uv run nox -s test
```

This will try to test with all compatible Python versions that `nox` can find. To run the tests with only a particular version, run something like this:

```shell
uv run nox -s test-3.13
```

It is good to run the tests locally before making a PR, but it is not necessary to have all Python versions run. It is rare for a failure to appear in a single version, and the CI will catch it anyway.

## Code quality

Parsita uses Ruff and mypy to ensure a minimum standard of code quality. The code quality commands are encapsulated with Nox:

```shell
uv run nox -s format
uv run nox -s lint
uv run nox -s type_check
```

## Generating the docs

Parsita uses MkDocs to generate HTML docs from Markdown. For development purposes, they can be served locally without needing to build them first:

```shell
uv run mkdocs serve
```

To deploy the current docs to GitHub Pages, Parsita uses the MkDocs `gh-deploy` command that builds the static site on the `gh-pages` branch, commits, and pushes to the origin:

```shell
uv run mkdocs gh-deploy
```

## Making a release

1. Bump
    1. Increment version in `pyproject.toml`
    2. Run `uv lock`
    3. Commit with message "Bump version number to X.Y.Z"
    4. Push commit to GitHub
    5. Check [CI](https://github.com/drhagen/parsita/actions/workflows/ci.yml) to ensure all tests pass
2. Tag
    1. Tag commit with "vX.Y.Z"
    2. Push tag to GitHub
    3. Wait for [build](https://github.com/drhagen/parsita/actions/workflows/release.yml) to finish
    4. Check [PyPI](https://pypi.org/project/parsita/) for good upload
3. Publish to conda-forge
    1. Fork [parsita-feedstock](https://github.com/conda-forge/parsita-feedstock)
    2. Create branch with name `vX.Y.Z`
    3. Update `recipe/meta.yaml`
        * Update version
        * Update sha256 to match source tarball on PyPI
        * Reset build number to 0
        * Update `requirements` and other project metadata
    4. Commit with message "updated vX.Y.Z"
    5. Push to fork
    6. Open PR on upstream
    7. Wait for build to succeed
    8. Squash merge PR
4. Document
    1. Create [GitHub release](https://github.com/drhagen/parsita/releases) with name "Parsita X.Y.Z" and major changes in body
    2. If appropriate, deploy updated docs
