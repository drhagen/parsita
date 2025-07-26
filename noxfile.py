from nox import Session, options, parametrize
from nox_uv import session

options.default_venv_backend = "uv"
options.sessions = ["test", "coverage", "lint", "type_check"]


@session(python=["3.10", "3.11", "3.12", "3.13"], uv_groups=["test"])
def test(s: Session):
    coverage_file = f".coverage.{s.python}"
    s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests")


@session(venv_backend="none")
def coverage(s: Session):
    s.run("coverage", "combine")
    s.run("coverage", "html")
    s.run("coverage", "xml", "--fail-under=100")


@session(venv_backend="none")
@parametrize("command", [["ruff", "check", "."], ["ruff", "format", "--check", "."]])
def lint(s: Session, command: list[str]):
    s.run(*command)


@session(venv_backend="none")
def type_check(s: Session):
    s.run("mypy", "src", "examples")


@session(venv_backend="none")
def format(s: Session):
    s.run("ruff", "check", ".", "--select", "I", "--select", "RUF022", "--fix")
    s.run("ruff", "format", ".")
