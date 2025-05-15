from setuptools import setup, find_packages

setup(
    name="fdd_pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.25.0",
        "boto3>=1.24.0",
        "pandas>=2.0.0",
        "plotly>=5.15.0",
        "dash>=2.14.0",
        "python-dotenv>=1.0.0",
        "huggingface-hub>=0.17.0",
        "PyMuPDF>=1.22.0"
    ],
    entry_points={
        "console_scripts": [
            "fdd-process=fdd_pipeline.orchestrator:main",
            "fdd-dashboard=fdd_pipeline.dashboard:main",
        ],
    },
)