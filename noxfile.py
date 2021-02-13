import platform

import nox_poetry


@nox_poetry.session(python=['3.6', '3.7', '3.8', '3.9'])
def test(session: nox_poetry.Session):
    if platform.system() == "Windows":
        site_packages = f'{session.virtualenv.location}/Lib/site-packages'
    else:
        site_packages = f'{session.virtualenv.location}/lib/python{session.python}/site-packages'

    session.install('.')
    session.install('pytest', 'pytest-cov', 'pytest-timeout')
    session.env['COVERAGE_FILE'] = f'.coverage.{session.python}'
    session.run('python', '-m', 'pytest', '--cov', f'{site_packages}/parsita')


@nox_poetry.session(venv_backend='none')
def coverage(session):
    session.install('coverage[toml]')
    session.run('coverage', 'combine')
    session.run('coverage', 'html')


@nox_poetry.session(venv_backend='none')
def lint(session):
    session.install('flakehell', 'flake8', 'pep8-naming', 'flake8-quotes')
    session.run('flakehell', 'lint', 'src', 'tests', 'examples')
