Populate Gitlab Project Variables from .env file
=================================================

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
