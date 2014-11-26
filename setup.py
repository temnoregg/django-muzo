from os.path import join
from setuptools import setup, find_packages


def get_version():
    with open(join('muzo', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


setup(
    name='django-muzo',
    version=get_version(),
    description='Django GP payment module',
    author='Petr Chalupny',
    author_email='temnoregg@gmail.com',
    url='https://github.com/temnoregg/django-muzo',
    packages=find_packages(),
    install_requires=['Django>=1.2'],
    zip_safe=False
)