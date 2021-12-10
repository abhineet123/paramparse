import setuptools

with open("ReadMe.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="paramparse",
    version="1.7.1",
    author="Abhineet Singh",
    author_email="abhineet.iiita@gmail.com",
    description="argparse wrapper to allow hierarchically nested class based parameters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abhineet123/paramparse",
    include_package_data=True,
    py_modules=["paramparse", "docstring_parser_custom"],
    packages=setuptools.find_packages(),
    install_requires=[
    ],
    python_requires='>3.5.2',
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

)
