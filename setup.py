#!/usr/bin/env python3
"""
🚀 InternMailing - Setup Script
=================================
Setup script for InternMailing - Academic & Corporate Outreach System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="internmailing",
    version="2.1.0",
    author="InternMailing Team",
    author_email="support@internmailing.com",
    description="AI-powered academic and corporate outreach system for students and professionals",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Flamechargerr/InternMailing",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Email",
        "Topic :: Education",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "internmailing=system:main",
            "internmailing-corporate=corporate_outreach:demo_corporate_outreach",
        ],
    },
    keywords="email outreach academic research internship job referral networking ai",
    project_urls={
        "Bug Reports": "https://github.com/Flamechargerr/InternMailing/issues",
        "Documentation": "https://github.com/Flamechargerr/InternMailing/wiki",
        "Source": "https://github.com/Flamechargerr/InternMailing",
    },
)