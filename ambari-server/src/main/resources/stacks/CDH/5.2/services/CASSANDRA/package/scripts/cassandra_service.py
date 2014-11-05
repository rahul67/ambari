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

Ambari Agent

"""

import json
import os
import signal

from resource_management import *
from os.path import isfile


def cassandra_service(action='start'): # start or stop
  import params
  
  cassandra_pid_file = format("{cassandra_pid_file}")

  if action == 'start':
    command = format("service {cassandra_service_name} start")
    Execute(command)   
  elif action == 'stop':
    # attempt to grab the pid in case we need it later
    cassandra_pid = 0    
    if isfile(cassandra_pid_file):   
      with open(cassandra_pid_file, "r") as file:
        try:
          cassandra_pid = int(file.read())
          Logger.info("Cassandra is running with a PID of {0}".format(cassandra_pid))
        except:
          Logger.info("Unable to read PID file {0}".format(cassandra_pid_file))
        finally:
          file.close()

    command = format("service {cassandra_service_name} stop")  
    Execute(command)

    # on SUSE, there is a bug where Cassandra doesn't kill the process 
    # but this could also affect any OS, so don't restrict this to SUSE
    if cassandra_pid > 0:
      try:
        os.kill(cassandra_pid, 0)
      except:
        Logger.info("The Cassandra process has successfully terminated")
      else:
        Logger.info("The Cassandra process with ID {0} failed to terminate; explicitly killing.".format(cassandra_pid))
        os.kill(cassandra_pid, signal.SIGKILL)

    # in the event that the Cassandra scripts don't remove the pid file
    if isfile( cassandra_pid_file ):   
      Execute(format("rm -f {cassandra_pid_file}"))
        
def clean_initial():
    Execute(format("rm -Rf {default_cassandra_dir}/*"))

