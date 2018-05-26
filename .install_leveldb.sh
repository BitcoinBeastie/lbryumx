#!/bin/bash
sudo add-apt-repository -y ppa:giskou/librocksdb
sudo apt-get -qq update
sudo apt-get install -yq librocksdb libsnappy-dev zlib1g-dev libbz2-dev libgflags-dev
wget https://launchpad.net/ubuntu/+archive/primary/+files/leveldb_1.20.orig.tar.gz
tar -xzvf leveldb_1.20.orig.tar.gz
pushd leveldb-1.20 && make && sudo mv out-shared/libleveldb.* /usr/local/lib && sudo cp -R include/leveldb /usr/local/include && sudo ldconfig && popd
