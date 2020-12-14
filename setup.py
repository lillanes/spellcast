from setuptools import setup

VERSION = "0.1.0"

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(
    name="spellcast",
    author="León Illanes",
    author_email="lillanes@cs.toronto.edu",
    url="https://github.com/lillanes/spellcast",
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
        'Twisted>=20.3.0',
        ],
    packages=["spellcast"],
    entry_points={
        "console_scripts": ['spellcast = spellcast.spellcast:main',
                            'cast = spellcast.spellcast:main']
        },
    version=VERSION,
    description="Casts a video to a DLNA media renderer in the local network.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    )
