import re

import setuptools

with open("pytapo/version.py", encoding="utf-8") as version_file:
    version_match = re.search(r'PYTAPO_VERSION\s*=\s*["\']([^"\']+)', version_file.read())
if not version_match:
    raise RuntimeError("PYTAPO_VERSION not found")

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytapo",
    version=version_match.group(1),
    author="Juraj Nyíri",
    author_email="juraj.nyiri@gmail.com",
    description="Python library for communication with Tapo Cameras",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AaronRohrbacher/pytapo",
    project_urls={"Upstream": "https://github.com/JurajNyiri/pytapo"},
    packages=setuptools.find_packages(),
    install_requires=[
        "aiofiles",
        "requests",
        "urllib3",
        "pycryptodome",
        "rtp",
        "python-kasa",
    ],
    tests_require=["pytest", "pytest-asyncio", "mock"],
    extras_require={"test": ["pytest", "pytest-asyncio", "mock"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
