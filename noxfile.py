import nox

nox.options.sessions = ["test", "flake8", "pydocstyle"]
nox.options.reuse_existing_virtualenvs = True
PYTHON_VERSIONS = ["2.7", "3.5", "3.6", "3.7"]


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """Run tests."""
    args = ["pip", "install", "codecov"]
    session.run(*args)

    session.install("-r", "requirements-test.txt")
    args = ["coverage", "run", "setup.py", "test"]
    session.run(*args)

    args = ["coverage", "report"]
    session.run(*args)

    args = ["codecov"]
    session.run(*args)


@nox.session(python=PYTHON_VERSIONS)
def flake8(session):
    """Run flake8."""
    session.install("-r", "requirements-test.txt")
    args = ["flake8", "laterpay", "setup.py", "tests"]
    session.run(*args)


@nox.session(python=PYTHON_VERSIONS)
def pydocstyle(session):
    """Run pydocstyle."""
    session.install("-r", "requirements-test.txt")
    args = ["pydocstyle"]
    session.run(*args)
