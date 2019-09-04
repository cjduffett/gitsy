# gitsy - Write Yourself a Git!

## Prerequisites

* Install `make`
* Install `poetry` system-wide
* Install `pyenv` system-wide
  * `pyenv install 3.7.2`
  * `pyenv local 3.7.2`

## Installation

Create a Python virtual environment in your local project directory, using `poetry` to install all project dependencies, dev dependencies, and scripts:

```
make .venv
```

To run the `gitsy` script activate the virtual environment:

```
source ./.venv/bin/activate
```

And run `gitsy`:

```
(.venv): gitsy version
```

## VSCode Settings

To ensure all developers have the same, consistent versions of all linters, formatters, and other dev tools we must specifically tell VSCode to use the dev tools installed in our project's `.venv` directory. VSCode may also sense the `.venv` directory automatically.

