""" used for packaging this for pypi """

import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="pygoodwe",
    version="0.0.16",
    author="James Hodgkinson",
    author_email="yaleman@ricetek.net",
    description="Goodwe Python interface",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/yaleman/pygoodwe",
    packages=setuptools.find_packages(),
    install_requires=['requests'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
