"""
Package installation configuration for maharera-agent-extractor.
"""

from setuptools import setup, find_packages
from pathlib import Path

long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name="maharera-agent-extractor",
    version="1.0.0",
    author="PureFrame Lab",
    description="Automated MahaRERA real-estate agent data extractor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    packages=find_packages(exclude=["tests*", "scripts*", "data*"]),
    install_requires=[
        "playwright>=1.44.0",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.3",
        "lxml>=5.2.2",
        "pytesseract>=0.3.10",
        "Pillow>=10.3.0",
        "2captcha-python>=1.3.0",
        "aiosqlite>=0.20.0",
        "openpyxl>=3.1.3",
        "pydantic>=2.7.1",
        "python-dotenv>=1.0.1",
        "tenacity>=8.3.0",
        "tqdm>=4.66.4",
        "loguru>=0.7.2",
        "click>=8.1.7",
    ],
    extras_require={
        "dev": [
            "pytest>=8.2.2",
            "pytest-asyncio>=0.23.7",
            "pytest-mock>=3.14.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "maharera-extract=main:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
