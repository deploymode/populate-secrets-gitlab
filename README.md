Populate Gitlab Project Variables from .env file
=================================================

## Install

```shell
# From git (in any project)
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
populate-gitlab list --environment uat --gitlab-host gitlab.example.com --project my-group/my-project

# Show all values including masked secrets
populate-gitlab list --environment uat --gitlab-host gitlab.example.com --project my-group/my-project --sensitive
```

### Write variables from .env file

```shell
populate-gitlab write \
  --env-file path/to/.env \
  --environment uat \
  --gitlab-host gitlab.example.com \
  --project my-group/my-project \
  --mask \
  --exclude APP_NAME,LOG_CHANNEL
```

### Get/export variables

```shell
populate-gitlab get --environment uat --gitlab-host gitlab.example.com --project my-group/my-project --export
```
