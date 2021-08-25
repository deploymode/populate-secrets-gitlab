import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="populate_secrets_gitlab",
    version="0.2.0",
    author="Joe Niland",
    author_email="joe@deploymode.com",
    description="Populate Gitlab CI/CD Variables from .env file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deploymode/populate-secrets-gitlab",
    project_urls={
        "Bug Tracker": "https://github.com/deploymode/populate-secrets-gitlab/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["python-gitlab==2.10.0", "python-dotenv==0.19.0"],
    setup_requires=["flake8"],
    entry_points={
        "console_scripts": [
            "populate-gitlab = populate_secrets_gitlab.__main__:main",
        ],
    },
)
