#!/usr/bin/env python
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from resource_management import *
from ambari_commons import OSCheck

config = Script.get_config()

cosmos_pid_dir = config['configurations']['cosmos-env']['pid_dir']
cosmos_collectd_pid_file = config['configurations']['cosmos-env']['cosmos_collectd_pid_file']
cosmos_jmx_pid_file = config['configurations']['cosmos-env']['cosmos_jmx_pid_file']

hostname = config['hostname']
tmp_dir = Script.get_tmp_dir()
