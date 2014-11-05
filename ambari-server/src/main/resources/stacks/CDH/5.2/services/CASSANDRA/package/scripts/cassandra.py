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

Ambari Agent

"""
import os

from resource_management import *
import sys


def cassandra():
  import params

  Directory(params.config_dir,
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

  configFile("cassandra.yaml", template_name="cassandra.yaml.j2")

  Directory(params.cassandra_pid_dir,
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

  Directory(params.cassandra_log_dir,
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

  Directory(params.data_file_directories.split(","),
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

  Directory(params.commitlog_directory,
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

  Directory(params.saved_caches_directory,
            owner=params.cassandra_user,
            recursive=True,
            group=params.cassandra_group
  )

def configFile(name, template_name=None):
  import params

  File(format("{config_dir}/{name}"),
       content=Template(template_name),
       owner=params.cassandra_user,
       group=params.cassandra_group
  )




