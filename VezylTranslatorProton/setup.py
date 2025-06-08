# setup.py
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("locale_module.py", compiler_directives={"language_level": "3"}),
)
