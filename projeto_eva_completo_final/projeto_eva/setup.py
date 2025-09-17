"""
Script de setup para o projeto EVA.
"""

from setuptools import setup, find_packages
import os

# Ler README para descrição longa
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Ler requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="eva-assistant",
    version="1.0.0",
    author="Equipe EVA",
    author_email="contato@eva-assistant.com",
    description="EVA - Assistente de IA Pessoal com Consciência Distribuída",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/eva-assistant/eva",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "gpu": [
            "nvidia-ml-py3>=7.352.0",
        ],
        "voice": [
            "piper-tts>=1.2.0",
            "coqui-tts>=0.15.0",
        ],
        "web": [
            "gradio>=3.40.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "eva=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    zip_safe=False,
)
