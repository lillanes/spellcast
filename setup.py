from setuptools import setup

version = "0.1.0"


setup(
    name="mage",
    packages=["mage"],
    entry_points={
        "console_scripts": ['mage = mage.mage:main']
        },
    version=version,
    description="Casts a video to a DLNA media renderer in the network.",
    author="León Illanes",
    author_email="lillanes@cs.toronto.edu",
    url="https://github.com/lillanes/mage"
    )
