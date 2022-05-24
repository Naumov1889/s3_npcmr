import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="s3_npcmr",
    version="0.0.1",
    author="Maksim",
    author_email="maksim.naumov1889@gmail.com",
    description="A set of use cases of boto3 wrapped into a module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Naumov1889/s3_npcmr",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "s3_npcmr"},
    packages=setuptools.find_packages(where="s3_npcmr"),
    python_requires=">=3.6",
    install_requires=[
        'boto3==1.16.40',
        'botocore==1.19.40',
        'redis>=3.5.3, <3.6',
    ],
)