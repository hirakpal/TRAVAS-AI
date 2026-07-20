#!/usr/bin/env python
"""Setup script for TRAVAS-AI"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="travas-ai",
    version="0.1.0",
    author="Hirak Pal",
    author_email="hirakpal@gmail.com",
    description="Travel + AI Agent System - Intelligent travel assistant with specialized agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hirakpal/TRAVAS-AI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.22.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "pylint>=3.0.3",
            "isort>=5.13.2",
            "mypy>=1.7.1",
        ],
        "db": [
            "sqlalchemy>=2.0.23",
            "psycopg2-binary>=2.9.9",
        ]
    },
    entry_points={
        "console_scripts": [
            "travas=main:cli",
        ],
    },
)
