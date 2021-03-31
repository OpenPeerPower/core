#!/usr/bin/env python3
"""Open Peer Power setup script."""
from datetime import datetime as dt

from setuptools import find_packages, setup

import openpeerpower.const as opp_const

PROJECT_NAME = "Open Peer Power"
PROJECT_PACKAGE_NAME = "openpeerpower"
PROJECT_LICENSE = "Apache License 2.0"
PROJECT_AUTHOR = "The Open Peer Power Authors"
PROJECT_COPYRIGHT = f" 2013-{dt.now().year}, {PROJECT_AUTHOR}"
PROJECT_URL = "https://www.openpeerpower.io/"
PROJECT_EMAIL = "hello@openpeerpower.io"

PROJECT_GITHUB_USERNAME = "openpeerpower"
PROJECT_GITHUB_REPOSITORY = "core"

PYPI_URL = f"https://pypi.python.org/pypi/{PROJECT_PACKAGE_NAME}"
GITHUB_PATH = f"{PROJECT_GITHUB_USERNAME}/{PROJECT_GITHUB_REPOSITORY}"
GITHUB_URL = f"https://github.com/{GITHUB_PATH}"

DOWNLOAD_URL = f"{GITHUB_URL}/archive/{opp_const.__version__}.zip"
PROJECT_URLS = {
    "Bug Reports": f"{GITHUB_URL}/issues",
    "Dev Docs": "https://developers.openpeerpower.io/",
}

PACKAGES = find_packages(exclude=["tests", "tests.*"])

REQUIRES = [
    "aiohttp==3.7.4",
    "astral==1.10.1",
    "async_timeout==3.0.1",
    "attrs==19.3.0",
    "awesomeversion==21.2.3",
    "bcrypt==3.1.7",
    "certifi>=2020.12.5",
    "ciso8601==2.1.3",
    "httpx==0.16.1",
    "jinja2>=2.11.3",
    "PyJWT==1.7.1",
    # PyJWT has loose dependency. We want the latest one.
    "cryptography==3.3.2",
    "pip>=8.0.3,<20.3",
    "python-slugify==4.0.1",
    "pytz>=2021.1",
    "pyyaml==5.4.1",
    "requests==2.25.1",
    "ruamel.yaml==0.15.100",
    "voluptuous==0.12.1",
    "voluptuous-serialize==2.4.0",
    "yarl==1.6.3",
]

MIN_PY_VERSION = ".".join(map(str, opp_const.REQUIRED_PYTHON_VER))

setup(
    name=PROJECT_PACKAGE_NAME,
    version=opp_const.__version__,
    url=PROJECT_URL,
    download_url=DOWNLOAD_URL,
    project_urls=PROJECT_URLS,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    python_requires=f">={MIN_PY_VERSION}",
    test_suite="tests",
    entry_points={"console_scripts": ["opp = openpeerpower.__main__:main"]},
)
