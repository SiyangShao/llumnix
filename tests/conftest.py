# Copyright (c) 2024, Alibaba Group;
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import time
import shutil
import os
import subprocess
import ray
from ray._raylet import PlacementGroupID
from ray._private.utils import hex_to_binary
from ray.util.placement_group import (
    PlacementGroup,
    placement_group_table,
    remove_placement_group,
)

import pytest

from llumnix.utils import random_uuid


def cleanup_ray_env_func():
    try:
        # list_placement_groups cannot take effects.
        for placement_group_info in placement_group_table().values():
            try:
                pg = PlacementGroup(
                    PlacementGroupID(hex_to_binary(placement_group_info["placement_group_id"]))
                )
                remove_placement_group(pg)
            # pylint: disable=bare-except
            except:
                pass
    # pylint: disable=bare-except
    except:
        pass

    try:
        named_actors = ray.util.list_named_actors(True)
        for actor in named_actors:
            try:
                actor_handle = ray.get_actor(actor['name'], namespace=actor['namespace'])
                ray.kill(actor_handle)
            # pylint: disable=bare-except
            except:
                continue
    # pylint: disable=bare-except
    except:
        pass

    try:
        # Should to be placed after killing actors, otherwise it may occur some unexpected errors when re-init ray.
        ray.shutdown()
    # pylint: disable=bare-except
    except:
        pass

@pytest.fixture
def ray_env():
    subprocess.run(["ray", "start", "--head", "--disable-usage-stats", "--port=6379"], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)
    ray.init(namespace="llumnix", ignore_reinit_error=True)
    yield
    cleanup_ray_env_func()
    time.sleep(1.0)
    subprocess.run(["ray", "stop"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)

def backup_error_log(func_name):
    curr_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    dst_dir = os.path.expanduser(f'/mnt/error_log/{curr_time}_{random_uuid()}')
    os.makedirs(dst_dir, exist_ok=True)

    src_dir = os.getcwd()

    for filename in os.listdir(src_dir):
        if filename.startswith("instance_"):
            src_file = os.path.join(src_dir, filename)
            shutil.copy(src_file, dst_dir)

        elif filename.startswith("bench_"):
            src_file = os.path.join(src_dir, filename)
            shutil.copy(src_file, dst_dir)

    file_path = os.path.join(dst_dir, 'test.info')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f'{func_name}')

    print(f"Backup error instance log to directory {dst_dir}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        func_name = item.name
        backup_error_log(func_name)
