import io
import re

from distutils.core import setup


with io.open("pyghostbt/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setup(
    name="pyghostbt",
    version=version,
    author="strengthening",
    author_email="ducg@foxmail.com",
    # url='http://www.you.com/projectname',
    packages=["pyghostbt"],
)
