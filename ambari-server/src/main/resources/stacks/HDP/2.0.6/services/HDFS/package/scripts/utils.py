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
import os
import re
import tempfile
import shutil
import urllib2

from resource_management import *
from resource_management.libraries.functions.format import format
from resource_management.core.shell import call, checked_call
from resource_management.core.exceptions import ComponentIsNotRunning

from zkfc_slave import ZkfcSlave

def safe_zkfc_op(action, env):
  """
  Idempotent operation on the zkfc process to either start or stop it.
  :param action: start or stop
  :param env: environment
  """
  zkfc = None
  if action == "start":
    try:
      zkfc = ZkfcSlave()
      zkfc.status(env)
    except ComponentIsNotRunning:
      if zkfc:
        zkfc.start(env)

  if action == "stop":
    try:
      zkfc = ZkfcSlave()
      zkfc.status(env)
    except ComponentIsNotRunning:
      pass
    else:
      if zkfc:
        zkfc.stop(env)


def failover_namenode():
  """
  Failover the primary namenode by killing zkfc if it exists on this host (assuming this host is the primary).
  """
  import params
  check_service_cmd = format("hdfs haadmin -getServiceState {namenode_id}")
  code, out = call(check_service_cmd, verbose=True, logoutput=True, user=params.hdfs_user)

  state = "unknown"
  if code == 0 and out:
    state = "active" if "active" in out else ("standby" if "standby" in out else state)
    Logger.info("Namenode service state: %s" % state)

  if state == "active":
    Logger.info("Rolling Upgrade - Initiating namenode failover by killing zkfc on active namenode")

    # Forcefully kill ZKFC on this host to initiate a failover
    kill_zkfc(params.hdfs_user)

    # Wait until it transitions to standby
    check_standby_cmd = format("hdfs haadmin -getServiceState {namenode_id} | grep standby")
    Execute(check_standby_cmd,
            user=params.hdfs_user,
            tries=30,
            try_sleep=6)
  else:
    Logger.info("Rolling Upgrade - Host %s is the standby namenode." % str(params.hostname))


def kill_zkfc(zkfc_user):
  """
  There are two potential methods for failing over the namenode, especially during a Rolling Upgrade.
  Option 1. Kill zkfc on primary namenode provided that the secondary is up and has zkfc running on it.
  Option 2. Silent failover (not supported as of HDP 2.2.0.0)
  :param zkfc_user: User that started the ZKFC process.
  """
  import params
  if params.dfs_ha_enabled:
    zkfc_pid_file = get_service_pid_file("zkfc", zkfc_user)
    if zkfc_pid_file:
      check_process = format("ls {zkfc_pid_file} > /dev/null 2>&1 && ps -p `cat {zkfc_pid_file}` > /dev/null 2>&1")
      code, out = call(check_process, verbose=True)
      if code == 0:
        Logger.debug("ZKFC is running and will be killed to initiate namenode failover.")
        kill_command = format("{check_process} && kill -9 `cat {zkfc_pid_file}` > /dev/null 2>&1")
        checked_call(kill_command)


def get_service_pid_file(name, user):
  """
  Get the pid file path that was used to start the service by the user.
  :param name: Service name
  :param user: User that started the service.
  :return: PID file path
  """
  import params
  pid_dir = format("{hadoop_pid_dir_prefix}/{user}")
  pid_file = format("{pid_dir}/hadoop-{user}-{name}.pid")
  return pid_file


def service(action=None, name=None, user=None, options="", create_pid_dir=False,
            create_log_dir=False):
  """
  :param action: Either "start" or "stop"
  :param name: Component name, e.g., "namenode", "datanode", "secondarynamenode", "zkfc"
  :param user: User to run the command as
  :param options: Additional options to pass to command as a string
  :param create_pid_dir: Create PID directory
  :param create_log_dir: Crate log file directory
  """
  import params

  options = options if options else ""
  pid_dir = format("{hadoop_pid_dir_prefix}/{user}")
  pid_file = format("{pid_dir}/hadoop-{user}-{name}.pid")
  log_dir = format("{hdfs_log_dir_prefix}/{user}")
  check_process = format(
    "ls {pid_file} >/dev/null 2>&1 &&"
    " ps -p `cat {pid_file}` >/dev/null 2>&1")

  if create_pid_dir:
    Directory(pid_dir,
              owner=user,
              recursive=True)
  if create_log_dir:
    Directory(log_dir,
              owner=user,
              recursive=True)

  hadoop_env_exports = {
    'HADOOP_LIBEXEC_DIR': params.hadoop_libexec_dir
  }

  if params.security_enabled and name == "datanode":
    ## The directory where pid files are stored in the secure data environment.
    hadoop_secure_dn_pid_dir = format("{hadoop_pid_dir_prefix}/{hdfs_user}")
    hadoop_secure_dn_pid_file = format("{hadoop_secure_dn_pid_dir}/hadoop_secure_dn.pid")

    # At Champlain stack and further, we may start datanode as a non-root even in secure cluster
    if not (params.hdp_stack_version != "" and compare_versions(params.hdp_stack_version, '2.2') >= 0) or params.secure_dn_ports_are_in_use:
      user = "root"
      pid_file = format(
        "{hadoop_pid_dir_prefix}/{hdfs_user}/hadoop-{hdfs_user}-{name}.pid")

    if action == 'stop' and (params.hdp_stack_version != "" and compare_versions(params.hdp_stack_version, '2.2') >= 0) and \
      os.path.isfile(hadoop_secure_dn_pid_file):
        # We need special handling for this case to handle the situation
        # when we configure non-root secure DN and then restart it
        # to handle new configs. Otherwise we will not be able to stop
        # a running instance 
        user = "root"
        
        try:
          check_process_status()
          
          custom_export = {
            'HADOOP_SECURE_DN_USER': params.hdfs_user
          }
          hadoop_env_exports.update(custom_export)
          
        except ComponentIsNotRunning:
          pass

  hadoop_daemon = format("{hadoop_bin}/hadoop-daemon.sh")

  if user == "root":
    cmd = [hadoop_daemon, "--config", params.hadoop_conf_dir, action, name]
    if options:
      cmd += [options, ]
    daemon_cmd = as_sudo(cmd)
  else:
    cmd = format("{ulimit_cmd} {hadoop_daemon} --config {hadoop_conf_dir} {action} {name}")
    if options:
      cmd += " " + options
    daemon_cmd = as_user(cmd, user)
     
  service_is_up = check_process if action == "start" else None
  #remove pid file from dead process
  File(pid_file,
       action="delete",
       not_if=check_process
  )
  Execute(daemon_cmd,
          not_if=service_is_up,
          environment=hadoop_env_exports
  )

  if action == "stop":
    File(pid_file,
         action="delete",
    )


def get_port(address):
  """
  Extracts port from the address like 0.0.0.0:1019
  """
  if address is None:
    return None
  m = re.search(r'(?:http(?:s)?://)?([\w\d.]*):(\d{1,5})', address)
  if m is not None:
    return int(m.group(2))
  else:
    return None


def is_secure_port(port):
  """
  Returns True if port is root-owned at *nix systems
  """
  if port is not None:
    return port < 1024
  else:
    return False

def fetch_libhadoop():
    import params
    if params.overwrite_native:

      hdp_native_lib_link_name = os.readlink(params.hdp_native_lib_link)
      hdp_native_lib_path = os.path.join(os.path.dirname(params.hdp_native_lib_link), hdp_native_lib_link_name)
      lib_backup = hdp_native_lib_path + ".hdp"
      libhadoop_cdh_name_suffix_dest = ".cdh-" + params.libhadoop_cdh_version
      
      # If libhadoop native library is NOT already replaced with CDH, then overwrite.
      if not hdp_native_lib_link_name.find(libhadoop_cdh_name_suffix_dest):
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
