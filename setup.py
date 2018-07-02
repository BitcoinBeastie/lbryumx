from setuptools import setup

setup(
    name='lbryumx',
    version='0.0.1',
    url='https://github.com/lbryio/lbryumx',
    license='MIT',
    author='LBRY Inc.',
    author_email='hello@lbry.io',
    description='Server for the LBRY Wallet.',
    keywords='server,wallet,crypto,currency,money,bitcoin,lbry',
    classifiers=(
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Topic :: Utilities',
    ),
    packages=('lbryumx',),
    python_requires='>=3.6',
    install_requires=(
        'msgpack',
        'beaker',
        'lbryschema',
        'electrumx',
    ),
    extras_require={
        'test': (
            'mock',
            'pytest',
            'pytest-asyncio',
            'pytest-xprocess',
            'pytest-cov',
        )
    }
)
