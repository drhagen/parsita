import nox_poetry


@nox_poetry.session(python=['3.6', '3.7', '3.8', '3.9'])
def test(session: nox_poetry.Session):
    session.install('.')
    session.install('pytest', 'pytest-cov', 'pytest-timeout')
    session.env['COVERAGE_FILE'] = f'.coverage.{session.python}'
    session.run('python', '-m', 'pytest', '--cov', 'parsita')


@nox_poetry.session(venv_backend='none')
def coverage(session: nox_poetry.Session):
    session.install('coverage[toml]')
    session.run('coverage', 'combine')
    session.run('coverage', 'html')
    session.run('coverage', 'xml')


@nox_poetry.session(venv_backend='none')
def lint(session: nox_poetry.Session):
    session.install('flakehell', 'flake8', 'pep8-naming', 'flake8-quotes')
    session.run('flakehell', 'lint', 'src', 'tests', 'examples')
