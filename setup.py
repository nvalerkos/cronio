import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cronio",
    version="1.0.0",
    author="Nikolas Valerkos",
    author_email="n.valerkos@gmail.com",
    description="This project has a sender and a receiver, the sender sends commands through RabbitMQ on the queue of a worker (receiver), the receiver executes them either with OS or Python2.7",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nvalerkos/cronio",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
