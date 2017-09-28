from setuptools import setup, find_packages
from setuptools.extension import Extension

setup(
    name='pelican_html',
    version='1.0.0a1',
    description=('...'),
    long_description=('...'),
    url='...',
    author='Vincent La',
    author_email='vincela9@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],
    keywords='pelican',
    packages=find_packages(exclude=['example', 'docs', 'setup', 'tests*']),
    include_package_data=True
)