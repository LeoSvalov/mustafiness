"""
Setup script for Mustafiness.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README_NEW.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="mustafiness",
    version="2.0.0",
    author="Mustafiness",
    author_email="mustafiness@example.com",
    description="A comprehensive Python library for collecting and analyzing Fantasy Premier League data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mustafiness",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mustafiness=cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="fantasy premier league fpl football soccer data analysis api",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mustafiness/issues",
        "Source": "https://github.com/yourusername/mustafiness",
        "Documentation": "https://github.com/yourusername/mustafiness#readme",
    },
)
