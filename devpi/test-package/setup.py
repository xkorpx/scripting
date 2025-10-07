from setuptools import setup, find_packages

setup(
    name="hello-devpi-test",
    version="0.0.1",
    description="A simple test package",
    author="leroy jenkins",
    author_email="test@blah.com",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ],
)
