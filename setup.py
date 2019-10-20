import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name='drf-redsys',
    version='0.1',
    packages=['drf-redsys'],
    description='Redsys payments with optional preauthorization and 1-Click',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Albert Lopez Alcacer',
    author_email='alcacer.la.1001@gmail.com',
    url='https://github.com/Alcasser/drf-redsys/',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    license='MIT',
    install_requires=[
        'Django>=2.0',
        'djangorestframework>=3.0.0',
        'pydes>=2.0.1',
        'zeep>=3.2.0',
        'xmltodict>=0.12.0'
    ]
)
