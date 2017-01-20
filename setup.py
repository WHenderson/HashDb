from setuptools import setup

setup(
    name='hashdb2',
    version='0.2',
    description='HashDb2 provides a simple method for executing commands based on matched files',
    url='https://github.com/WHenderson/HashDb',
    author='Will Henderson',
    author_email='whenderson.github@gmail.com',
    license='Apache 2.0',
    packages=['hashdb2'],
    zip_safe=False,
    install_requires=[
        'docopt>=0.6.2'
    ]
)
