#!/usr/bin/env python
"""
Caring Caribou Next
===================
- This work was initiated as part of the research project HEAVENS (HEAling Vulnerabilities to ENhance Software Security and Safety), and was forked to act as a quick way to perform changes for personal use, and for people that are intrested on those changes.
- While caringcaribounext is not perfect, it can act as a quick evaluation utility, which can help with exploration of a target ECU over several target networks/interfaces. This project is not meant to be a complete one button solution, but a tool that can give researchers a quick and easy head start into the path of ECU exploration.
"""

from setuptools import find_packages, setup

version = "1.1"
dl_version = "master" if "dev" in version else "v{}".format(version)

print(r"""-----------------------------------
 Installing Caring Caribou Next version {0}
-----------------------------------
""".format(version))

setup(
    name="caringcaribounext",
    version=version,
    author="Thomas Sermpinis",
    author_email="thomas.sermpinis@cr0wsplace.com",
    description="A fork of a friendly automotive security exploration tool",
    long_description=__doc__,
    keywords=["automotive", "security", "CAN", "automotive protocols", "fuzzing"],
    url="https://github.com/Cr0wTom/caringcaribounext",
    download_url="https://github.com/Cr0wTom/caringcaribounext/releases",
    license="GPLv3",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "python-can"
    ],
    entry_points={
        "console_scripts": [
            "ccn.py=caringcaribounext.caringcaribounext:main",
            "caringcaribounext=caringcaribounext.caringcaribounext:main",
        ],
        "caringcaribounext.modules": [
            "dcm = caringcaribounext.modules.dcm",
            "doip = caringcaribounext.modules.doip",
            "dump = caringcaribounext.modules.dump",
            "fuzzer = caringcaribounext.modules.fuzzer",
            "listener = caringcaribounext.modules.listener",
            "send = caringcaribounext.modules.send",
            "test = caringcaribounext.modules.test",
            "uds_fuzz = caringcaribounext.modules.uds_fuzz",
            "uds = caringcaribounext.modules.uds",
            "xcp = caringcaribounext.modules.xcp",
        ]
    }
)

print(r"""-----------------------------------------------------------
 Installation completed, run `ccn.py --help` to get started
-----------------------------------------------------------
""")
