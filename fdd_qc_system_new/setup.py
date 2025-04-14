"""
Setup script for the FDD Verification package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fdd_verification",
    version="1.0.0",
    author="FDD Verification Team",
    author_email="info@fddverification.com",
    description="A system for verifying FDD headers in PDF documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fddverification/fdd_verification",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMuPDF>=1.18.0",
        "numpy>=1.19.0",
        "torch>=1.9.0",
        "transformers>=4.5.0",
        "nltk>=3.6.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "flake8>=3.9.0",
        ],
    },
)
