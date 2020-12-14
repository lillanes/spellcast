from setuptools import setup

VERSION = "0.1.0"

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="spellcast",
    packages=["spellcast"],
    entry_points={
        "console_scripts": ['spellcast = spellcast.spellcast:main']
        "console_scripts": ['cast = spellcast.spellcast:main']
        },
    version=VERSION,
    description="Casts a video to a DLNA media renderer in the local network.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="León Illanes",
    author_email="lillanes@cs.toronto.edu",
    url="https://github.com/lillanes/spellcast"
    )
