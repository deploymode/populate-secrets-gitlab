Populate Gitlab Project Variables from .env file
=================================================

## Prerequisites

* Python3
* virtualenv

## Set up

```shell
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage Example

```shell
export GITLAB_TOKEN=...
python3 __init__.py \
	path/to/.env \
	uat \
	https://my-gitlab.example.com \
	project_id \
	--exclude APP_NAME,LOG_CHANNEL,DB_CONNECTION,BROADCAST_DRIVER,MAIL_FROM_NAME,MIX_SENTRY_LARAVEL_DSN,AZURE_REDIRECT_URI,MIX_APP_ENV \
	--debug
```
