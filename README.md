[![Build Status](https://travis-ci.org/lbryio/lbryumx.svg?branch=master)](https://travis-ci.org/lbryio/lbryumx)
[![Coverage Status](https://coveralls.io/repos/github/lbryio/lbryumx/badge.svg)](https://coveralls.io/github/lbryio/lbryumx)
[![Docker Automated build](https://img.shields.io/docker/build/lbry/lbryumx.svg)](https://hub.docker.com/r/lbry/lbryumx/builds/)

# LbryumX - The LBRY Electrum Protocol Server

![LbryumX running](images/screenshot.jpg "LbryumX screenshot")

LbryumX is an extension of [electrumx](https://github.com/kyuupichan/electrumx) that provides the server side of LBRY Electrum Protocol.

## Running from Docker

Installing from Docker is the best way to have a monitored and always up-to-date server. Watchtower ensures the Docker container will be running and checks for image updates every 5 minutes. To install it, just try:
```bash
sudo docker run -d --name watchtower  -v /var/run/docker.sock:/var/run/docker.sock \
    v2tec/watchtower --label-enable --cleanup
```

Then, [install and run lbrycrd](https://github.com/lbryio/lbrycrd#installation) with `-txindex`:
```bash
./lbrycrdd -server -txindex -rpcuser=lbry -rpcpassword=mySuperSecurePassword -port=19245
```

Finally, start the server:
```
sudo docker run -v database:/database --ulimit nofile=90000:90000 \
    -e DB_DIRECTORY=/database --net="host" \
    -e DAEMON_URL=http://lbry:mySuperSecurePassword@127.0.0.1:19245 \
    -d --label=com.centurylinklabs.watchtower.enable=true lbry/lbryumx:latest
```

This will create a volume called database, set the number of open files higher, use the host networking, set the RPC URL and label it as a watchtower monitored container. For more information on the available environment variables, see [electrumx documentation](https://electrumx.readthedocs.io/en/latest/environment.html). Environment variables are set on the container using `-e` as you can see in the above command.

## Installing from source on a Python virtual environment

1. Make sure you have [Python 3.6 installed](https://docs.python.org/3/using/windows.html#installing-python).
2. Create a new [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/).
3. Clone and install electrumx (this fork just makes it available as a module)
    ```bash
    $ git clone -b packages https://github.com/lbryio/electrumx.git electrumx
    $ pip install -e electrumx/.
    ```
4. Clone and install lbryumx:
    ```bash
    $ git clone https://github.com/lbryio/lbryumx.git
    $ pip install -r requirements.txt
    $ pip install -e .
    ```

## Usage

Lbryumx connects to an instance of [lbrycrd](https://github.com/lbryio/lbrycrd#installation) and provides an electrum protocol server with wallet commands and custom commands for claims. For using it, you will need a [lbry daemon](https://github.com/lbryio/lbry/tree/master/lbrynet) or any [final release of the LBRY app](https://lbry.io/get).

### Example Usage

Given that you have installed a [LBRY daemon](https://github.com/lbryio/lbry/tree/master/lbrynet) or a [LBRY app](https://lbry.io/get), edit `~/.lbrynet/daemon_settings.yml` for setting your server as the default one:
```
lbryum_servers:
    - my.lbryumx.server:50001
```
Then start and use the app or daemon normally.

## Running from Source

For running the server, all configurations are set over environment variables then we just run `lbryumx_server.py`, for instance:
```
TCP_PORT=50001 HOST=0.0.0.0 COIN=LBC DAEMON_URL=http://lbry:lbry@localhost:9245/ DB_DIRECTORY=/tmp/testx BANDWIDTH_LIMIT=10000 MAX_SESSIONS=1000 python3.6 lbryumx_server.py
```

If you're still stuck, [create an issue](https://github.com/lbryio/lbryumx/issues/new) with the output of that command, your system info, and any other information you think might be helpful.

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

The Travis CI system makes sure that every pull request is built, and that unit and sanity tests are automatically run. Then, after a success round of tests, a new Docker image is published.

## License

This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Security

We take security seriously. Please contact security@lbry.io regarding any security issues.
Our PGP key is [here](https://keybase.io/lbry/key.asc) if you need it.

## Contact

The primary contact for this project is [@shyba](https://github.com/shyba) (vshyba@lbry.io)
