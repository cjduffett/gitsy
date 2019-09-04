# gitsy - The Wannabe Git Clone

## Prerequisites

* Install [make](http://man7.org/linux/man-pages/man1/make.1.html), [poetry](https://poetry.eustace.io/), and [pyenv](https://github.com/pyenv/pyenv) on your system.
* Run `pyenv install 3.7.2` to install Python version 3.7.2, used by this project.

## Installation

### Create a Virtual Environment

Create a Python virtual environment in your local project directory using the `.venv` make target:
```
make .venv
```

This command uses the [venv](https://docs.python.org/3/library/venv.html) package that ships with Python 3.4+ to create the virtual environment, and uses poetry to install project dependencies from the lockfile.

### Activate that Virtual Environment

To run the `gitsy` CLI script, simply activate the virtual environment:
```
source ./.venv/bin/activate
```

And run `gitsy`:
```
(.venv): gitsy version
```

## Tests

To run the `gitsy` test suite, run [pytest](https://pytest.org/en/latest/) from within the virtual environment:
```
(.venv): pytest
```

This will discover and execute all tests in the `tests/` directory.

