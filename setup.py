from setuptools import setup, find_packages

setup(
    name="screenM",
    version="1.0.0",
    author="Antton Alberdi",
    author_email="antton.alberdi@sund.ku.dk",
    description="Data screener for genome-resolved metagenomics",
    packages=find_packages(), 
    include_package_data=True,
    install_requires=[
        "numpy",
        "pandas",
        "argparse",
        "PyYAML",
        "plotly",
        "biopython"
    ],
    entry_points={
        "console_scripts": [
            "screenm=screenm.cli:main",
        ],
    },
    python_requires=">=3.12",
)
