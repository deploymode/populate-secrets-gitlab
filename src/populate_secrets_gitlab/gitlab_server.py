import gitlab
import util

def gitlab_client(gitlab_host, gitlab_token):
    return gitlab.Gitlab(util.prepare_gitlab_host(gitlab_host), private_token=gitlab_token)

    