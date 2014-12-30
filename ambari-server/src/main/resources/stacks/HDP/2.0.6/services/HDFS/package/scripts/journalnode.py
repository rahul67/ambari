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
from resource_management.libraries.functions.version import compare_versions, format_hdp_stack_version
from resource_management.libraries.functions.format import format

from utils import service, fetch_libhadoop
from hdfs import hdfs


class JournalNode(Script):
  def install(self, env):
    import params

    self.install_packages(env, params.exclude_packages)
    fetch_libhadoop()
    env.set_params(params)

  def pre_rolling_restart(self, env):
    Logger.info("Executing Rolling Upgrade pre-restart")
    import params
    env.set_params(params)

    if params.version and compare_versions(format_hdp_stack_version(params.version), '2.2.0.0') >= 0:
      Execute(format("hdp-select set hadoop-hdfs-journalnode {version}"))

  def start(self, env, rolling_restart=False):
    import params

    env.set_params(params)
    self.configure(env)
    Directory(params.hadoop_pid_dir_prefix,
              mode=0755,
              owner=params.hdfs_user,
              group=params.user_group
    )
    service(
      action="start", name="journalnode", user=params.hdfs_user,
      create_pid_dir=True,
      create_log_dir=True
    )

  def stop(self, env, rolling_restart=False):
    import params

    env.set_params(params)
    service(
      action="stop", name="journalnode", user=params.hdfs_user,
      create_pid_dir=True,
      create_log_dir=True
    )

  def configure(self, env):
    import params

    Directory(params.jn_edits_dir,
              recursive=True,
              owner=params.hdfs_user,
              group=params.user_group
    )
    env.set_params(params)
    hdfs()
    pass

  def status(self, env):
    import status_params

    env.set_params(status_params)
    check_process_status(status_params.journalnode_pid_file)


if __name__ == "__main__":
  JournalNode().execute()
