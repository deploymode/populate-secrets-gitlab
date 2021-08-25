#############################################################
# Populate values from .env file to Gitlab Project-Level vars.
#
# Excluded variables are defined in `ci.env`
#
#############################################################

from dotenv import dotenv_values
import gitlab
import urllib
import argparse
import os
from traceback import print_exc


def main():
    # If the var name contains any of these words it will be masked
    varsToMask = ["KEY", "SECRET"]  # PASSWORD
    enableMasking = False
    gitlabToken = None

    parser = argparse.ArgumentParser(description="Populate parameter store")
    parser.add_argument("envFilePath", metavar="E", help="Path to .env file")
    parser.add_argument(
        "environment", metavar="X", help="Name of gitlab environment, e.g. `uat`"
    )
    parser.add_argument("gitlabServer", metavar="S", help="Gitlab server host")
    parser.add_argument("projectNameOrId", metavar="P", help="Gitlab Project name")
    parser.add_argument(
        "--include",
        required=False,
        default="",
        help="Environment variables to include when writing. Excludes all others. CSV list, e.g. NODE_ENV,MY_VAR",
    )
    parser.add_argument(
        "--exclude",
        required=False,
        default="",
        help="Environment variables to exclude from writing. CSV list, e.g. NODE_ENV,MY_VAR",
    )
    parser.add_argument("--debug", action="store_true", help="Produce debug output")

    args = parser.parse_args()

    try:
        gitlabToken = os.environ["GITLAB_TOKEN"]
    except KeyError:
        raise Exception(
            "GITLAB_TOKEN must be set. Get token from https://your-gitlab.example.com/profile/personal_access_tokens"
        )

    # Create gitlab client
    gitlabClient = gitlab.Gitlab(args.gitlabServer, private_token=gitlabToken)
    if args.debug:
        gitlabClient.enable_debug()

    print("Loading env vars from {}".format(args.envFilePath))

    env_path = args.envFilePath
    env_values = dotenv_values(dotenv_path=env_path)

    env_vars_to_include = []
    env_vars_to_exclude = []

    if len(args.include) > 0:
        env_vars_to_include = args.include.split(",")
        print("Including: {}".format("; ".join(env_vars_to_include)))

    if len(args.exclude) > 0:
        env_vars_to_exclude = args.exclude.split(",")
        print("Excluding: {}".format("; ".join(env_vars_to_exclude)))

    gitlabProject = ""

    try:
        gitlabProject = gitlabClient.projects.get(
            id=urllib.parse.quote_plus(args.projectNameOrId)
        )
    except gitlab.exceptions.GitlabHttpError:
        raise Exception(
            "Could not find project: {}".format(
                urllib.parse.quote_plus(args.projectNameOrId)
            )
        )

    if not gitlabProject:
        raise Exception("Could not find project: {}".format(args.projectNameOrId))

    # gitlabProjectVariables = gitlabProject.variables.list()
    # if args.debug:
    #     print(*gitlabProjectVariables, sep='\n')
    # gitlabProjectVariableKeys = list(map(lambda o: o.key, gitlabProjectVariables))
    # if args.debug:
    #     print(*gitlabProjectVariableKeys, sep='\n')

    for key, value in env_values.items():
        isUpdate = False
        if len(env_vars_to_include) > 0 and key not in env_vars_to_include:
            continue

        if key in env_vars_to_exclude:
            print("Skipping {}".format(key))
            continue

        # Write to Gitlab API
        try:
            projectVar = None
            # Check if var exists in the current environment
            try:
                projectVar = gitlabProject.variables.get(
                    key
                )  # , 'filter[environment_scope]'='{}'.format(args.environment))
                if args.debug:
                    print(projectVar)
            except gitlab.exceptions.GitlabGetError:
                # Do nothing - API returned a 404
                print("{} var not found - will create".format(key))

            if args.debug:
                print(projectVar)

            if projectVar and projectVar.environment_scope == args.environment:
                isUpdate = True
                # Update
                projectVar.value = value
                projectVar.save()
            else:
                # Add
                payload = {
                    "key": key,
                    "value": value,
                    "environment_scope": args.environment,
                }

                if enableMasking and any(x in key for x in varsToMask):
                    payload["masked"] = True

                if args.debug:
                    print(payload)

                gitlabProject.variables.create(payload)
        except gitlab.exceptions.GitlabHttpError:
            print("Failed to write {} due to error from Gitlab API".format(key))
            print_exc()
            continue
        except Exception:
            print("Failed to write {} due to unexpected error".format(key))
            print_exc()
            continue

        print(
            "Wrote {} variable {} to Gitlab API in environment {}".format(
                "updated" if isUpdate else "new", key, args.environment
            )
        )

    print("Done")


if __name__ == "__main__":
    main()
