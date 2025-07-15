#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from idna.idnadata import scripts
from setuptools import setup

with open("README.md") as readme_file:
    README = readme_file.read()

setup(
    name="ska_tangoctl",
    version="0.6.1",
    description="",
    long_description=README + "\n\n",
    author="Team Atlas",
    author_email="johan.coetzer@tsolo.io",
    url="https://gitlab.com/ska-telescope/ska-tangoctl",
    packages=setuptools.find_namespace_packages(where="src", include=["*"]),
    package_dir={"": "src"},
    include_package_data=True,
    license="BSD license",
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite="tests",
    install_requires=["numpy", "pytango"],
    setup_requires=[],  # TODO add this package's dependencies to the list
    tests_require=["pytest", "pytest-cov" "pytest-json-report", "pycodestyle"],
    extras_require={},
    data_files = [("man/man1", ["man/man1/tangoctl.1", "man/man1/tangoktl.1"])],
    scripts = [
        "src/ska_tangoctl/tango_control/tangoctl.py",
        "src/ska_tangoctl/tango_kontrol/tangoktl.py"
    ]
)
