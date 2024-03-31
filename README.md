[![CI](https://github.com/lpenz/pthugefileviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/lpenz/pthugefileviewer/actions/workflows/ci.yml)
[![coveralls](https://coveralls.io/repos/github/lpenz/pthugefileviewer/badge.svg?branch=main)](https://coveralls.io/github/lpenz/pthugefileviewer?branch=main)
[![PyPI](https://img.shields.io/pypi/v/pthugefileviewer)](https://pypi.org/project/pthugefileviewer/)
[![github](https://img.shields.io/github/v/release/lpenz/pthugefileviewer?logo=github)](https://github.com/lpenz/pthugefileviewer/releases)


# pthugefileviewer

*pthugefileviewer* is a control for [prompt-toolkit] that can display
huge files. It does so by mmap'ing the file and only reading the lines
shown in the screen. It avoids any operation that would require
reading the whole file, like counting the lines.


## Installation


### Releases

pthugefileviewer can be installed via [pypi]:

```
pip install pthugefileviewer
```

For [nix] users, it is also available as a [flake].


### Repository

We can also clone the github repository and install pthugefileviewer from it with:

```
pip install .
```

We can also install it for the current user only by running instead:

```
pip install --user .
```


## Development

pthugefileviewer uses the standard python3 infra. To develop and test the module:
- Clone the repository and go into the directory:
  ```
  git clone git@github.com:lpenz/pthugefileviewer.git
  cd pthugefileviewer
  ```
- Use [`venv`] to create a local virtual environment with
  ```
  python -m venv venv
  ```
- Activate the environment by running the shell-specific `activate`
  script in `./venv/bin/`. For [fish], for instance, run:
  ```
  source ./venv/bin/activate.fish
  ```
- Install pthugefileviewer in "editable mode":
  ```
  pip install -e '.[test]'
  ```
- To run the tests:
  ```
  pytest
  ```
  Or, to run the tests with coverage:
  ```
  pytest --cov
  ```
- Finally, to exit the environment and clean it up:
  ```
  deactivate
  rm -rf venv
  ```


[pypi]: https://pypi.org/project/pthugefileviewer/
[nix]: https://nixos.org/
[flake]: https://nixos.wiki/wiki/Flakes
[`venv`]: https://docs.python.org/3/library/venv.html
[prompt-toolkit]: https://github.com/prompt-toolkit/python-prompt-toolkit
