from setuptools import setup, find_packages
import os

# Package name based on directory
package_name = "cntsci" if os.path.basename(os.getcwd()) == "cntsci" else "cntsci_app"

setup(
    name=package_name,
    version="1.0.0",
    description="Application Bureau CNTSCI - Gestion Matériel, Automobile et Personnel",
    author="M. SESS Eddy",
    author_email="eddy@cntsci.ci",
    license="Propriétaire - CNTSCI 2025",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "psycopg2-binary>=2.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            f"cntsci={package_name}.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
    ],
)
