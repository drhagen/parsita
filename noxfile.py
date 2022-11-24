import nox_poetry


@nox_poetry.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
def test(session: nox_poetry.Session):
    session.install(".", "pytest", "pytest-cov", "pytest-timeout")
    session.env["COVERAGE_FILE"] = f".coverage.{session.python}"
    session.run("python", "-m", "pytest", "--cov", "parsita")


@nox_poetry.session(venv_backend="none")
def coverage(session: nox_poetry.Session):
    session.run("coverage", "combine")
    session.run("coverage", "html")
    session.run("coverage", "xml")


@nox_poetry.session(venv_backend="none")
def black(session: nox_poetry.Session):
    session.run("black", "--check", ".")


@nox_poetry.session(venv_backend="none")
def isort(session: nox_poetry.Session):
    session.run("isort", "--check", ".")


@nox_poetry.session(venv_backend="none")
def flake8(session: nox_poetry.Session):
    session.run("pflake8", "src", "tests", "examples")
