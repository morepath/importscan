import io
from setuptools import setup, find_packages

long_description = "\n".join(
    (
        io.open("README.rst", encoding="utf-8").read(),
        io.open("CHANGES.txt", encoding="utf-8").read(),
    )
)

setup(
    name="importscan",
    version="0.2",
    description="Recursively import modules and sub-packages",
    long_description=long_description,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    keywords="decorator import package",
    author="Martijn Faassen",
    author_email="faassen@startifact.com",
    url="http://importscan.readthedocs.io",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["setuptools"],
    extras_require=dict(
        test=["pytest >= 2.9.0", "pytest-remove-stale-bytecode"],
        coverage=["pytest-cov"],
        pep8=["flake8", "black"],
    ),
)
