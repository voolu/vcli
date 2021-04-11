from setuptools import setup, find_packages
from io import open
from os import path

import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# automatically captured required modules for install_requires in requirements.txt
with open(path.join(HERE, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if
                    ('git+' not in x) and (not x.startswith('#')) and (not x.startswith('-'))]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if 'git+' not in x]

scripts = ['vhost', 'vsh', 'vcp', 'vacc']

setup(
    name='voolu',
    description='SSH is so last year.',
    version='0.0.7',
    packages=find_packages(),  # list of all packages
    install_requires=install_requires,
    python_requires='>=3.7',  # any python greater than 3.6
    scripts=[f'{script}.py' for script in scripts],
    entry_points={
        'console_scripts': [f'{script}={script}:cli' for script in scripts],
    },
    author="Voolu Cloud",
    long_description=README,
    long_description_content_type="text/markdown",
    license='MIT',
    url='https://github.com/voolu/vcli',
    dependency_links=dependency_links,
    author_email='support@voolu.io',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
    ]
)
