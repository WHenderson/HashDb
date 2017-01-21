from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()
setup(
    name='hashdb2',
    version='0.3',
    description='HashDb2 provides a simple method for executing commands based on matched files',
    long_description=readme(),
    classifiers=[
        'Development Status :: 1 - Planning0',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: System :: Filesystems',
        'Topic :: Database',
        'Topic :: Utilities'
    ],
    keywords='file matching comparison same identical duplicate duplicates',
    url='https://github.com/WHenderson/HashDb',
    author='Will Henderson',
    author_email='whenderson.github@gmail.com',
    license='Apache 2.0',
    packages=['hashdb2'],
    zip_safe=False,
    install_requires=[
        'docopt>=0.6.2'
    ],
    entry_points = {
        'console_scripts': ['hashdb2=hashdb2.command_line:main'],
    }
)
