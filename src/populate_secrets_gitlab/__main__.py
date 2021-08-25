#!/usr/bin/env python
"""The main entry point. Invoke as `populate-secrets-gitlab`
"""


def main():
    from .app import main

    main()


if __name__ == "__main__":
    main()
