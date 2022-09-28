#!/usr/bin/env python
"""The main entry point. Invoke as `populate-secrets-gitlab`
"""


def main():
    from .app import cli

    cli()


if __name__ == "__main__":
    main()
