from urllib.parse import urlparse

def prepare_gitlab_host(gitlab_host):
    url_parts = urlparse(gitlab_host)

    if not url_parts.scheme:
        return f"https://{gitlab_host}"

    return gitlab_host