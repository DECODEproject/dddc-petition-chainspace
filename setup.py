from setuptools import setup, find_packages

setup(
    name="dddc-petition-chainspace",
    version="0.1.0",
    author="Jim Barritt",
    author_email="jim@planet-ix.com",
    packages=find_packages(),
    install_requires=[
        "pytest_runner==4.4",
        "zenroom==0.1.3",
        "pre-commit==1.14.4",
        "python-multipart==0.0.5",
        "requests==2.21.0"
    ],
    tests_require=["pytest", "codecov", "requests", "pytest-cov"],
)
