import setuptools

with open("ReadMe.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="paramparse",
    version="1.2.6",
    author="Abhineet Singh",
    author_email="abhineet.iiita@gmail.com",
    description="argparse wrapper to allow hierarchically nested class based parameters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abhineet123/paramparse",
    include_package_data=True,
    py_modules=["paramparse"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
