[![Build Status](https://travis-ci.org/lbryio/lbryumx.svg?branch=master)](https://travis-ci.org/lbryio/lbryumx)
[![Coverage Status](https://coveralls.io/repos/github/lbryio/lbryumx/badge.svg)](https://coveralls.io/github/lbryio/lbryumx)

# LbryumX - The LBRY Electrum Protocol Server

![LbryumX running](images/screenshot.jpg "LbryumX screenshot")

LbryumX is an extension of [electrumx](https://github.com/kyuupichan/electrumx) that provides the server side of LBRY Electrum Protocol.

## Installing from Docker

Installing from Docker is the best way to have a monitored and always up-to-date server. Watchtower ensures the Docker container will be running and checks for image updates every 5 minutes. To install it, just try:
```bash
sudo docker run -d --name watchtower  -v /var/run/docker.sock:/var/run/docker.sock   v2tec/watchtower --label-enable --cleanup
```

Then, start the server:
```
sudo docker run -v database:/database --ulimit nofile=90000:90000 -e DB_DIRECTORY=/database --net="host" -d --label=com.centurylinklabs.watchtower.enable=true lbry/lbryumx:latest
```

This will create a volume called database, set the number of open files higher, use the host networking and label it as a watchtower monitored container. For more information on the available environment variables, see [electrumx documentation](https://electrumx.readthedocs.io/en/latest/environment.html).

## Installation

**fixme -- wip: explain further when released and packaging is in place**

## Usage

**fixme -- wip: explain further when released and packaging is in place**

### Example Usage

**fixme -- wip: explain further when released and packaging is in place**

## Running from Source

**fixme -- wip: explain further when released and packaging is in place**

If you encounter any errors, please check `doc/build-*.md` for further instructions. If you're still stuck, [create an issue](https://github.com/lbryio/lbryumx/issues/new) with the output of that command, your system info, and any other information you think might be helpful.

## Contributing

Contributions to this project are welcome, encouraged, and compensated. For more details, see [lbry.io/faq/contributing](https://lbry.io/faq/contributing)

The `master` branch is regularly built and tested, but is not guaranteed to be
completely stable. [Releases](https://github.com/lbryio/lbryumx/releases) are created
regularly to indicate new official, stable release versions.

Testing and code review is the bottleneck for development; we get more pull
requests than we can review and test on short notice. Please be patient and help out by testing
other people's pull requests, and remember this is a security-critical project where any mistake might cost people
lots of money.

Developers are strongly encouraged to write [unit tests](/doc/unit-tests.md) for new code, and to
submit new unit tests for old code. Unit tests can be run with: `py.test -v`

The Travis CI system makes sure that every pull request is built, and that unit and sanity tests are automatically run.

## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Security

We take security seriously. Please contact security@lbry.io regarding any security issues.
Our PGP key is [here](https://keybase.io/lbry/key.asc) if you need it.

## Contact

The primary contact for this project is [@shyba](https://github.com/shyba) (vshyba@lbry.io)
