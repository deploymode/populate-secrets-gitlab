#############################################################
# Manage Gitlab secrets
#
#############################################################

from dotenv import dotenv_values
import gitlab
from gitlab.v4.objects.projects import Project

from gitlab_server import gitlab_client
import click
import urllib
from urllib.parse import urlparse
import os
from traceback import print_exc
import logging

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s\t%(message)s',
        datefmt='%Y-%m-%d_%H:%M:%S.%s',
        handlers=[
            logging.StreamHandler()
        ],
    )
logger = logging.getLogger()

@click.group()
def cli():
    pass

@cli.command(help="Populate Gitlab project vars")
@click.option(
    "--env-file",
    required=True,
    help="Path to .env file",
)
@click.option(
    "--environment",
    required=True,
    help="Name of gitlab environment, e.g. `uat`",
)
@click.option(
    "--gitlab-host",
    required=True,
    help="Gitlab server host",
)
@click.option(
    "--project",
    required=True,
    help="Gitlab project name or ID",
)
@click.option(
    "--include",
    help="Environment variables to include when writing. Excludes all others. CSV list, e.g. NODE_ENV,MY_VAR",
    default=""
)
@click.option(
    "--exclude",
    help="Environment variables to exclude when writing. CSV list, e.g. NODE_ENV,MY_VAR",
    default=""
)
@click.option(
    "--mask",
    is_flag=True,
    default=False,
    help="Mask variables with strings KEY, SECRET, TOKEN in their name",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Produce debug output",
)
def write(env_file, environment, gitlab_host, project, include, exclude, mask, debug):
    # If the var name contains any of these words it will be masked
    varsToMask = ["KEY", "SECRET", "TOKEN"]  # PASSWORD
    enableMasking = mask

    try:
        gitlab_token = os.environ["GITLAB_TOKEN"]
    except KeyError:
        raise Exception(
            "GITLAB_TOKEN must be set. Get token from https://your-gitlab.example.com/profile/personal_access_tokens"
        )

    if not os.path.exists(env_file):
        raise Exception(f"Unable to find env file {env_file}")

    # Create gitlab client
    gitlabClient = gitlab_client(gitlab_host, gitlab_token)
    if debug:
        gitlabClient.enable_debug()

    logger.info("Loading env vars from {}".format(env_file))

    env_values = dotenv_values(dotenv_path=env_file)

    env_vars_to_include = []
    env_vars_to_exclude = []

    if len(include) > 0:
        env_vars_to_include = include.split(",")
        logger.info("Including: {}".format("; ".join(env_vars_to_include)))

    if len(exclude) > 0:
        env_vars_to_exclude = exclude.split(",")
        logger.info("Excluding: {}".format("; ".join(env_vars_to_exclude)))

    gitlabProject: Project

    try:
        gitlabProject = gitlabClient.projects.get(
            id=urllib.parse.quote_plus(project)
        )
    except gitlab.exceptions.GitlabHttpError:
        raise Exception(
            "Could not find project: {}".format(
                urllib.parse.quote_plus(project)
            )
        )

    if not gitlabProject:
        raise Exception("Could not find project: {}".format(project))

    # Get all existing vars
    gl_project_vars = gitlabProject.variables.list(get_all=True)
    logger.debug(gl_project_vars)
    gitlab_project_variable_keys_with_scope = list(map(lambda o: {"environment_scope": o.environment_scope, "key": o.key}, gl_project_vars))
    logger.debug(gitlab_project_variable_keys_with_scope)
    gitlab_project_variable_keys_by_scope = dict()
    for d in gitlab_project_variable_keys_with_scope:
        gitlab_project_variable_keys_by_scope.setdefault(
                    d["environment_scope"], []
                ).append(d["key"])

    logger.debug(gitlab_project_variable_keys_by_scope)

    for key, value in env_values.items():
        is_update = False
        if len(env_vars_to_include) > 0 and key not in env_vars_to_include:
            continue

        if key in env_vars_to_exclude:
            logger.info("Skipping {}".format(key))
            continue

        # Write to Gitlab API
        try:
            if key in gitlab_project_variable_keys_by_scope[environment]:
                is_update = True
                # Update
                project_var = [v for v in gl_project_vars if v.key == key][0]
                project_var.value = value
                if enableMasking and any(x in key for x in varsToMask):
                    project_var.masked = True
                project_var.save(filter={'environment_scope': environment})
            else:
                # Add
                payload = {
                    "key": key,
                    "value": value,
                    "environment_scope": environment,
                }

                if enableMasking and any(x in key for x in varsToMask):
                    payload["masked"] = True

                logger.debug(payload)

                gitlabProject.variables.create(payload)
        except gitlab.exceptions.GitlabHttpError:
            logger.info("Failed to write {} due to error from Gitlab API".format(key))
            print_exc()
            continue
        except Exception:
            logger.info("Failed to write {} due to unexpected error".format(key))
            print_exc()
            continue

        logger.info(
            "Wrote {} variable {} to Gitlab API in environment {}".format(
                "updated" if is_update else "new", key, environment
            )
        )

    logger.info("Done")

@cli.command(help="Get Gitlab project vars")
@click.option(
    "--environment",
    required=True,
    help="Name of gitlab environment, e.g. `uat`",
)
@click.option(
    "--gitlab-host",
    required=True,
    help="Gitlab server host",
)
@click.option(
    "--project",
    required=True,
    help="Gitlab project name or ID",
)
@click.option(
    "--export",
    is_flag=True,
    help="Export variables to file: $scope.env",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Produce debug output",
)
def get(environment, gitlab_host, project, export, debug):
    gitlab_token = None

    try:
        gitlab_token = os.environ["GITLAB_TOKEN"]
    except KeyError:
        raise Exception(
            f"GITLAB_TOKEN must be set. Get token from https://{gitlab_host}/-/profile/personal_access_tokens"
        )

    # Create gitlab client
    gitlabClient = gitlab_client(gitlab_host, gitlab_token) 
    if debug:
        gitlabClient.enable_debug()

    logger.info(f"Loading project vars from {project}")

    try:
        gitlabProject = gitlabClient.projects.get(
            id=urllib.parse.quote_plus(project)
        )
    except gitlab.exceptions.GitlabHttpError:
        raise Exception(
            "Could not find project: {}".format(
                urllib.parse.quote_plus(project)
            )
        )

    if not gitlabProject:
        raise Exception("Could not find project: {}".format(project))

    click.secho(f"Getting vars from {gitlabProject.name} ({gitlabProject.id})", fg='green')


    gitlabProjectVariables = gitlabProject.variables.list(get_all=True)
    for variable in gitlabProjectVariables:
        scope = 'global' if variable.environment_scope == '*' else variable.environment_scope
        if scope == environment or scope == 'global':
            click.secho(f"[{variable.environment_scope}] {variable.key}={variable.value}", fg='yellow')

            if export:
                logger.debug(f"Writing {variable.key} to {scope}.env")
                with open(f"{scope}.env", 'a+') as f:
                    f.write(f"{variable.key}={variable.value}\n")

    logger.info("Done")


if __name__ == "__main__":
    cli()
