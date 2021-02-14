from setuptools import setup, find_packages, find_namespace_packages

version = open('VERSION').read().strip()

setup(
    name='simplep4client',
    version=version,
    author='CommitThis Ltd',
    author_email='gdavey@committhis.co.uk',
    url='https://github.com/CommitThis/black-box-bmv2',
    description='Simple client for interfacing with P4 runtime servers',
    long_description=open('README.md').read(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],
    packages=find_namespace_packages(),
    setup_requires=[
        'wheel'
    ],
    install_requires=[
        'grpcio',
        'protobuf',
        'scapy',
        'ipaddress'
    ],
    scripts=[
        'bin/run_bmv2'
    ]
)