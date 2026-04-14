#############################################################
# Manage Gitlab secrets
#
#############################################################

from dotenv import dotenv_values
import gitlab
from gitlab.v4.objects.projects import Project

from .gitlab_server import gitlab_client
import click
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
        raise click.ClickException(
            f"GITLAB_TOKEN must be set. Get token from https://{gitlab_host}/-/profile/personal_access_tokens"
        )

    if not os.path.exists(env_file):
        raise click.ClickException(f"Env file not found: {env_file}")

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
        gitlabProject = gitlabClient.projects.get(id=project)
    except gitlab.exceptions.GitlabHttpError:
        raise Exception("Could not find project: {}".format(project))

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
        gitlabProject = gitlabClient.projects.get(id=project)
    except gitlab.exceptions.GitlabHttpError:
        raise Exception("Could not find project: {}".format(project))

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


@cli.command(name="list", help="List Gitlab project vars for an environment")
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
    "--sensitive",
    is_flag=True,
    default=False,
    help="Show all values including masked ones",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Produce debug output",
)
def list_vars(environment, gitlab_host, project, sensitive, debug):
    try:
        gitlab_token = os.environ["GITLAB_TOKEN"]
    except KeyError:
        raise click.ClickException(
            f"GITLAB_TOKEN must be set. Get token from https://{gitlab_host}/-/profile/personal_access_tokens"
        )

    gitlabClient = gitlab_client(gitlab_host, gitlab_token)
    if debug:
        gitlabClient.enable_debug()

    try:
        gitlabProject = gitlabClient.projects.get(id=project)
    except gitlab.exceptions.GitlabHttpError:
        raise click.ClickException(
            "Could not find project: {}".format(project)
        )

    if not gitlabProject:
        raise click.ClickException("Could not find project: {}".format(project))

    click.secho(
        f"Variables for {gitlabProject.name} ({gitlabProject.id}) — environment: {environment}",
        fg="green",
    )

    variables = gitlabProject.variables.list(get_all=True)

    env_vars = []
    for v in variables:
        scope = "global" if v.environment_scope == "*" else v.environment_scope
        if scope == environment or scope == "global":
            env_vars.append(v)

    if not env_vars:
        click.secho("No variables found.", fg="yellow")
        return

    # Determine column widths
    max_key_len = max(len(v.key) for v in env_vars)
    max_scope_len = max(len(v.environment_scope) for v in env_vars)

    for v in env_vars:
        if sensitive or not v.masked:
            display_value = v.value
        else:
            display_value = "********"

        scope_label = v.environment_scope
        key_col = v.key.ljust(max_key_len)
        scope_col = scope_label.ljust(max_scope_len)
        masked_label = " [masked]" if v.masked else ""

        click.echo(f"  {scope_col}  {key_col}  {display_value}{masked_label}")

    click.secho(f"\n{len(env_vars)} variable(s) found.", fg="green")


@cli.command(help="Download Gitlab project vars to an .env file")
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
    "--output-dir",
    default=".",
    help="Directory to save the .env file (default: current directory)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Produce debug output",
)
def download(environment, gitlab_host, project, output_dir, debug):
    try:
        gitlab_token = os.environ["GITLAB_TOKEN"]
    except KeyError:
        raise click.ClickException(
            f"GITLAB_TOKEN must be set. Get token from https://{gitlab_host}/-/profile/personal_access_tokens"
        )

    if not os.path.isdir(output_dir):
        raise click.ClickException(f"Output directory does not exist: {output_dir}")

    gitlabClient = gitlab_client(gitlab_host, gitlab_token)
    if debug:
        gitlabClient.enable_debug()

    try:
        gitlabProject = gitlabClient.projects.get(id=project)
    except gitlab.exceptions.GitlabHttpError:
        raise click.ClickException("Could not find project: {}".format(project))

    if not gitlabProject:
        raise click.ClickException("Could not find project: {}".format(project))

    click.secho(
        f"Downloading vars from {gitlabProject.name} ({gitlabProject.id}) — environment: {environment}",
        fg="green",
    )

    variables = gitlabProject.variables.list(get_all=True)

    env_vars = []
    for v in variables:
        scope = "global" if v.environment_scope == "*" else v.environment_scope
        if scope == environment or scope == "global":
            env_vars.append(v)

    if not env_vars:
        click.secho("No variables found.", fg="yellow")
        return

    output_path = os.path.join(output_dir, f"{environment}.env")

    if os.path.exists(output_path):
        click.secho(f"File already exists: {output_path}", fg="yellow")
        choice = click.prompt(
            "Choose action",
            type=click.Choice(["overwrite", "rename", "cancel"], case_sensitive=False),
            default="cancel",
        )
        if choice == "cancel":
            click.secho("Cancelled.", fg="red")
            return
        elif choice == "rename":
            n = 1
            while True:
                output_path = os.path.join(output_dir, f"{environment}-{n}.env")
                if not os.path.exists(output_path):
                    break
                n += 1

    with open(output_path, "w") as f:
        for v in env_vars:
            f.write(f"{v.key}={v.value}\n")

    click.secho(f"Saved {len(env_vars)} variable(s) to {output_path}", fg="green")


if __name__ == "__main__":
    cli()
