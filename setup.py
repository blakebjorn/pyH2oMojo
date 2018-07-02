import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyH2oMojo",
    version="0.1.0",
    author="Blake Anderson",
    author_email="blakebanders@gmail.com",
    description="H2O MOJO wrapper - allows predictions from python without the webserver overhead.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blakebjorn/pyH2oMojo",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    include_package_data=True
)