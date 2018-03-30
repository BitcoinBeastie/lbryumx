import json
import os
import pytest
from os import environ
from lbryumx.coin import LBC
from electrumx.server.storage import Storage
from electrumx.server.env import Env


@pytest.fixture()
def block_processor(tmpdir_factory):
    environ.clear()
    environ['DB_DIRECTORY'] = tmpdir_factory.mktemp('db', numbered=True).strpath
    environ['DAEMON_URL'] = ''
    env = Env(LBC)
    bp = LBC.BLOCK_PROCESSOR(env, None, None)
    yield bp
    for attr in dir(bp):  # hack to close dbs on tear down
        obj = getattr(bp, attr)
        if isinstance(obj, Storage):
            obj.close()


@pytest.fixture('module')
def block_infos():
    block_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    blocks = {}
    for block_file_name in os.listdir(block_data_path):
        if not block_file_name.startswith('block'): continue
        number = block_file_name.split('_')[1].replace('.json', '')
        block_file_path = os.path.join(block_data_path, block_file_name)
        with open(block_file_path, 'r') as block_file:
            blocks[number] = json.loads(block_file.read())
    return blocks
