<p align="center">
  <a href="https://github.com/astral-sh/uv" target="blank"><img src="https://github.com/astral-sh/uv/blob/8674968a17e5f2ee0dda01d17aaf609f162939ca/docs/assets/logo-letter.svg" height="100" alt="uv logo" /></a>
  <a href="https://pre-commit.com/" target="blank"><img src="https://pre-commit.com/logo.svg" height="100" alt="pre-commit logo" /></a>
  <a href="https://github.com/astral-sh/ruff" target="blank"><img src="https://raw.githubusercontent.com/astral-sh/ruff/8c20f14e62ddaf7b6d62674f300f5d19cbdc5acb/docs/assets/bolt.svg" height="100" alt="ruff logo" style="background-color: #ef5552" /></a>
  <a href="https://bandit.readthedocs.io/" target="blank"><img src="https://raw.githubusercontent.com/pycqa/bandit/main/logo/logo.svg" height="100" alt="bandit logo" /></a>
  <a href="https://docs.pytest.org/" target="blank"><img src="https://raw.githubusercontent.com/pytest-dev/pytest/main/doc/en/img/pytest_logo_curves.svg" height="100" alt="pytest logo" /></a>
</p>

<p align="center">
  <a href="https://docs.docker.com/" target="blank"><img src="https://www.docker.com/wp-content/uploads/2022/03/Moby-logo.png" height="60" alt="Docker logo" /></a>
  <a href="https://github.com/features/actions" target="blank"><img src="https://avatars.githubusercontent.com/u/44036562" height="60" alt="GitHub Actions logo" /></a>
</p>

# GRVT Python SDK

[![CodeQL](https://github.com/smarlhens/python-boilerplate/workflows/codeql/badge.svg)](https://github.com/smarlhens/python-boilerplate/actions/workflows/codeql.yml)
[![GitHub CI](https://github.com/smarlhens/python-boilerplate/workflows/ci/badge.svg)](https://github.com/smarlhens/python-boilerplate/actions/workflows/ci.yml)
[![GitHub license](https://img.shields.io/github/license/smarlhens/python-boilerplate)](https://github.com/smarlhens/python-boilerplate)

---

## Installation via pip

```bash
pip install grvt-pysdk
```

## Usage

There are various ways to use the GRVT Python SDK

- [GRVT CCXT](https://github.com/gravity-technologies/grvt-pysdk/blob/main/tests/pysdk/test_grvt_ccxt.py) - CCXT compatible client for GRVT (sync Rest API calls)
- [GRVT CCXT Pro](https://github.com/gravity-technologies/grvt-pysdk/blob/main/tests/pysdk/test_grvt_ccxt_pro.py) - CCXT Pro compatible client for GRVT (async Rest API calls)
- [GRVT CCXT WS](https://github.com/gravity-technologies/grvt-pysdk/blob/main/tests/pysdk/test_grvt_ccxt_ws.py) - CCXT Pro + Web Socket client, supports async Rest APIs + WS subscriptions + JSON RPC calls over Web Sockets.
- [GRVT API Sync](https://github.com/gravity-technologies/grvt-pysdk/blob/main/tests/pysdk/test_grvt_raw_sync.py) - Synchronous API client for GRVT
- [GRVT API Async](https://github.com/gravity-technologies/grvt-pysdk/blob/main/tests/pysdk/test_grvt_raw_async.py) - Asynchronous API client for GRVT

## Contributor's guide

### Table of Contents

- [GRVT Python SDK](#grvt-python-sdk)
  - [Installation via pip](#installation-via-pip)
  - [Usage](#usage)
  - [Contributor's guide](#contributors-guide)
    - [Table of Contents](#table-of-contents)
    - [Prerequisites](#prerequisites)
    - [Installation of code](#installation-of-code)
    - [What's in the box ?](#whats-in-the-box-)
      - [uv](#uv)
      - [pre-commit](#pre-commit)
      - [ruff](#ruff)
      - [mypy](#mypy)
      - [bandit](#bandit)
      - [docformatter](#docformatter)
      - [Testing](#testing)
      - [Makefile](#makefile)

---

### Prerequisites

- [Python](https://www.python.org/downloads/) **>=3.10.0 <3.13** (_tested with 3.10.15_)
- [pre-commit](https://pre-commit.com/#install)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) **>=0.3.3** (_tested with 0.4.0_)
- [docker](https://docs.docker.com/get-docker/) (_optional_)

---

### Installation of code

1. Clone the git repository

   ```bash
   git clone https://github.com/grvt-technologies/grvt-pysdk.git
   ```

2. Go into the project directory

   ```bash
   cd grvt-pysdk/
   ```

3. Checkout working branch

   ```bash
   git checkout <branch>
   ```

4. Install dependencies

   ```bash
   make install
   ```

5. Enable pre-commit hooks

   ```bash
   pre-commit install
   ```

---

### What's in the box ?

#### uv

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package and project manager, written in Rust.

**pyproject.toml file** ([`pyproject.toml`](pyproject.toml)): orchestrate your project and its dependencies
**uv.lock file** ([`uv.lock`](uv.lock)): ensure that the package versions are consistent for everyone
working on your project

For more configuration options and details, see the [configuration docs](https://docs.astral.sh/uv/).

#### pre-commit

[pre-commit](https://pre-commit.com/) is a framework for managing and maintaining multi-language pre-commit hooks.

**.pre-commit-config.yaml file** ([`.pre-commit-config.yaml`](.pre-commit-config.yaml)): describes what repositories and
hooks are installed

For more configuration options and details, see the [configuration docs](https://pre-commit.com/).

#### ruff

[ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter, written in Rust.

Rules are defined in the [`pyproject.toml`](pyproject.toml).

For more configuration options and details, see the [configuration docs](https://github.com/astral-sh/ruff#configuration).

#### mypy

[mypy](http://mypy-lang.org/) is an optional static type checker for Python that aims to combine the benefits of
dynamic (or "duck") typing and static typing.

Rules are defined in the [`pyproject.toml`](pyproject.toml).

For more configuration options and details, see the [configuration docs](https://mypy.readthedocs.io/).

#### bandit

[bandit](https://bandit.readthedocs.io/) is a tool designed to find common security issues in Python code.

Rules are defined in the [`pyproject.toml`](pyproject.toml).

For more configuration options and details, see the [configuration docs](https://bandit.readthedocs.io/).

#### docformatter

[docformatter](https://github.com/PyCQA/docformatter) is a tool designed to format docstrings to
follow [PEP 257](https://peps.python.org/pep-0257/).

Options are defined in the [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

---

#### Testing

We are using [pytest](https://docs.pytest.org/) & [pytest-cov](https://github.com/pytest-dev/pytest-cov) to write tests.

To run tests with coverage:

```bash
make test
```

<details>

<summary>Output</summary>

```text
collected 4 items                                                                                                                                                                                                        

tests/pysdk/test_grvt_api_async.py::test_get_all_instruments PASSED                                                                                                                                                [ 25%]
tests/pysdk/test_grvt_api_async.py::test_open_orders PASSED                                                                                                                                                        [ 50%]
tests/pysdk/test_grvt_api_sync.py::test_get_all_instruments PASSED                                                                                                                                                 [ 75%]
tests/pysdk/test_grvt_api_sync.py::test_open_orders PASSED                                                                                                                                                         [100%]

---------- coverage: platform darwin, python 3.10.15-final-0 ----------
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/pysdk/__init__.py             1      0   100%
src/pysdk/grvt_api_async.py     152    113    26%
src/pysdk/grvt_api_base.py      158     75    53%
src/pysdk/grvt_api_sync.py      152    113    26%
src/pysdk/grvt_env.py            27      4    85%
src/pysdk/types.py              909      0   100%
-------------------------------------------------
TOTAL                          1399    305    78%


=================================================================================================== 4 passed in 1.20s ====================================================================================================
```

</details>

#### Makefile

We are using [Makefile](https://www.gnu.org/software/make/manual/make.html) to manage the project.

To see the list of commands:

```bash
make
```

```bash
➜  grvt-pysdk git:(main) ✗ make
help                           Show this help
run                            Run the project
test                           Run the tests
precommit                      Run the pre-commit hooks
lint                           Run the linter
format                         Run the formatter
typecheck                      Run the type checker
security                       Run the security checker
clean                          Clean the project
install                        Install the project
build                          Build the project
publish                        Publish the project
```

---
