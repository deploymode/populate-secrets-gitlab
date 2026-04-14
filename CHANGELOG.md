# Changelog

## [0.4.0](https://github.com/deploymode/populate-secrets-gitlab/compare/v0.3.0...v0.4.0) (2026-04-14)


### Features

* add download command and use setuptools-scm for versioning ([c96ee77](https://github.com/deploymode/populate-secrets-gitlab/commit/c96ee7704f3b0d9c7389000eb6113265e38fa93b))
* add list command and modernize packaging ([310790f](https://github.com/deploymode/populate-secrets-gitlab/commit/310790f929a35622f091d2f1a4546d4c296d0361))
* add read command ([b70e1c1](https://github.com/deploymode/populate-secrets-gitlab/commit/b70e1c11f7f72e300c76853db9ccb0bd46f49161))
* add read command ([4bf0dec](https://github.com/deploymode/populate-secrets-gitlab/commit/4bf0decda96eefd2700b1f0d5b3440315ccad64d))
* refactor - extract gitlab_server into module ([a7d5a4f](https://github.com/deploymode/populate-secrets-gitlab/commit/a7d5a4f4197a61831a22d47dd06308b6b6fa65d9))


### Bug Fixes

* remove double URL-encoding of project path ([8c28b4c](https://github.com/deploymode/populate-secrets-gitlab/commit/8c28b4c11ad9e4e721b4a873b02fcada82b50917))
* rename CLI entry point to populate-secrets-gitlab ([f0bd068](https://github.com/deploymode/populate-secrets-gitlab/commit/f0bd06847af001eaf338dcdb6b22f0a67b74b754))
* use ClickException for graceful error handling on missing env file and token ([e695310](https://github.com/deploymode/populate-secrets-gitlab/commit/e69531041a8108e1f87961764df8770d18db8a8c))
