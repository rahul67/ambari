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

from hdfs_datanode import datanode
from resource_management import *
from resource_management.libraries.functions.version import compare_versions, format_hdp_stack_version
from hdfs import hdfs

import tempfile
import shutil
import urllib2
import os



class DataNode(Script):
  def install(self, env):
    import params

    self.install_packages(env, params.exclude_packages)
    self.fetch_libhadoop(env)
    env.set_params(params)

  def pre_rolling_restart(self, env):
    Logger.info("Executing Rolling Upgrade pre-restart")
    import params
    env.set_params(params)

    if params.version and compare_versions(format_hdp_stack_version(params.version), '2.2.0.0') >= 0:
      Execute(format("hdp-select set hadoop-hdfs-datanode {version}"))

  def start(self, env, rolling_restart=False):
    import params

    env.set_params(params)
    self.configure(env)
    datanode(action="start")

  def stop(self, env, rolling_restart=False):
    import params

    env.set_params(params)
    datanode(action="stop")

  def configure(self, env):
    import params
    env.set_params(params)
    hdfs()
    datanode(action="configure")

  def status(self, env):
    import status_params

    env.set_params(status_params)
    check_process_status(status_params.datanode_pid_file)

  def fetch_libhadoop(self, env):
    import params
    tempdir=tempfile.mkdtemp()
    deb_name = tempdir + os.sep + "hadoop.deb"
    u = urllib2.urlopen(params.libhadoop_cdh_wheezy_pkg)
    f = open(deb_name, 'wb')
    meta = u.info()
    deb_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" %(deb_name, deb_size)
    
    chunk = 16 * 1024
    while True:
        buffer = u.read(chunk)
        if not buffer:
            break
        f.write(buffer)
    
    f.close()
    
    Execute(format("dpkg -x {deb_name} {tempdir}"))

    hdp_native_lib_link_name = os.readlink(params.hdp_native_lib_link)
    hdp_native_lib_path = os.path.join(os.path.dirname(params.hdp_native_lib_link), hdp_native_lib_link_name)
    lib_backup = hdp_native_lib_path + ".hdp"
    libhadoop_cdh_name_suffix_dest = ".cdh-" + params.libhadoop_cdh_version
    
    cdh_native_lib_link = os.path.join(tempdir, params.cdh_native_lib_link)
    cdh_native_lib_path = os.path.join(os.path.dirname(cdh_native_lib_link), os.readlink(cdh_native_lib_link))
    cdh_native_lib_path_dest = os.path.join(os.path.dirname(hdp_native_lib_path), os.path.basename(cdh_native_lib_path)) + libhadoop_cdh_name_suffix_dest

    if (os.path.isfile(cdh_native_lib_path)):
        os.rename(hdp_native_lib_path, lib_backup)
        shutil.move(cdh_native_lib_path, cdh_native_lib_path_dest)
        os.chdir(os.path.dirname(params.hdp_native_lib_link))
        lib_link_name = os.path.basename(params.hdp_native_lib_link)
        if (os.path.islink(lib_link_name)):
            os.unlink(lib_link_name)
        os.symlink(os.path.basename(cdh_native_lib_path_dest), lib_link_name)
    
    shutil.rmtree(tempdir)
    
if __name__ == "__main__":
  DataNode().execute()
