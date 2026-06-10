"""
DataFusion-CLI Setup
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="datafusion-cli",
    version="1.0.0",
    author="gitstq",
    author_email="",
    description="Lightweight Terminal Multi-Source Data Fusion & Intelligent Analysis Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/DataFusion-CLI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "datafusion=datafusion.cli:main",
        ],
    },
    keywords="data fusion, etl, data integration, cli, terminal, csv, json",
    project_urls={
        "Bug Reports": "https://github.com/gitstq/DataFusion-CLI/issues",
        "Source": "https://github.com/gitstq/DataFusion-CLI",
    },
)
