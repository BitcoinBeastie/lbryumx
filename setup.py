from setuptools import setup

setup(
    name='lbryumx',
    version='0.0.1',
    python_requires='>=3.6',
    install_requires=['msgpack', 'lbryschema', 'electrumx'],  # TODO: improve that
    tests_require=['pytest-runner', 'pytest'],
    packages=['lbryumx'],
    url='https://github.com/lbryio/lbryumx',
    license='MIT',
    author='LBRY Inc.',
    author_email='hello@lbry.io',
    description='Server for the Electrum Lightweight LBRY Wallet'
)
