Populate Gitlab Project Variables from .env file
=================================================

## Overview

A command-line tool for managing a Gitlab project's CI/CD variables, scoped to a
Gitlab [environment](https://docs.gitlab.com/ee/ci/environments/) (e.g. `uat`,
`production`). It talks to the Gitlab API using a personal access token and lets
you move variables between a local `.env` file and Gitlab in both directions.

It provides four commands:

- `write` — read a local `.env` file and create or update the matching
  project variables in the given environment scope. Supports `--include` /
  `--exclude` filtering and `--mask` to mask values whose key contains the
  substring `KEY`, `SECRET`, or `TOKEN` (e.g. `APP_KEY`, `PUBLIC_KEY`,
  `AUTH_TOKEN` will all be masked). Masking is one-way: an already-masked
  variable is never un-masked by this tool.
- `list` — print the variables for an environment in a table. Masked values are
  hidden unless you pass `--sensitive`.
- `get` — print the variables for an environment, optionally appending them to a
  `<scope>.env` file with `--export`.
- `download` — write an environment's variables to a `<environment>.env` file,
  prompting before overwriting an existing file.

All commands target both the requested environment and globally-scoped (`*`)
variables. Requires a `GITLAB_TOKEN` environment variable.

## Install

Install as a global user tool (isolated environment, command on your PATH):

```shell
# From git
uv tool install "git+https://github.com/deploymode/populate-secrets-gitlab.git"

# From a local checkout
uv tool install .
```

Run `uv tool update-shell` once if `~/.local/bin` is not yet on your PATH. `pipx install` works the same way if you prefer pipx.

To install into the current project's virtualenv instead of globally:

```shell
uv pip install "git+https://github.com/deploymode/populate-secrets-gitlab.git"
```

## Usage

Set your Gitlab personal access token:

```shell
export GITLAB_TOKEN=...
```

### List variables

```shell
# Show keys and non-masked values
populate-secrets-gitlab list --environment uat --gitlab-host gitlab.example.com --project my-group/my-project

# Show all values including masked secrets
populate-secrets-gitlab list --environment uat --gitlab-host gitlab.example.com --project my-group/my-project --sensitive
```

### Write variables from .env file

```shell
populate-secrets-gitlab write \
  --env-file path/to/.env \
  --environment uat \
  --gitlab-host gitlab.example.com \
  --project my-group/my-project \
  --mask \
  --exclude APP_NAME,LOG_CHANNEL
```

### Get/export variables

```shell
populate-secrets-gitlab get --environment uat --gitlab-host gitlab.example.com --project my-group/my-project --export
```

### Download variables to an .env file

```shell
populate-secrets-gitlab download --environment uat --gitlab-host gitlab.example.com --project my-group/my-project --output-dir .
```
