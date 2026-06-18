from populate_secrets_gitlab.util import prepare_gitlab_host


class TestPrepareGitlabHost:
    def test_bare_host_gets_https_prefix(self):
        assert prepare_gitlab_host("gitlab.example.com") == "https://gitlab.example.com"

    def test_https_host_unchanged(self):
        assert prepare_gitlab_host("https://gitlab.example.com") == "https://gitlab.example.com"

    def test_http_host_unchanged(self):
        assert prepare_gitlab_host("http://gitlab.example.com") == "http://gitlab.example.com"

    def test_trailing_slash_preserved(self):
        assert prepare_gitlab_host("https://gitlab.example.com/") == "https://gitlab.example.com/"

    def test_bare_host_with_trailing_slash(self):
        assert prepare_gitlab_host("gitlab.example.com/") == "https://gitlab.example.com/"
