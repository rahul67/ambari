#!/usr/bin/env python

'''
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
'''

import os.path
import logging
import subprocess
import platform
from ambari_commons.constants import AMBARI_SUDO_BINARY
from ambari_commons.shell import shellRunner
from Facter import Facter
from ambari_commons.os_check import OSConst, OSCheck
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl
logger = logging.getLogger()

class Hardware:
  SSH_KEY_PATTERN = 'ssh.*key'
  WINDOWS_GET_DRIVES_CMD ="foreach ($drive in [System.IO.DriveInfo]::getdrives()){$available = $drive.TotalFreeSpace;$used = $drive.TotalSize-$drive.TotalFreeSpace;$percent = ($used*100)/$drive.TotalSize;$size = $drive.TotalSize;$type = $drive.DriveFormat;$mountpoint = $drive.RootDirectory.FullName;echo \"$available $used $percent% $size $type $mountpoint\"}"

  def __init__(self):
    self.hardware = {}
    osdisks = Hardware.osdisks()
    self.hardware['mounts'] = osdisks
    otherInfo = Facter().facterInfo()
    self.hardware.update(otherInfo)
    pass

  @staticmethod
  def extractMountInfo(outputLine):
    if outputLine == None or len(outputLine) == 0:
      return None

      """ this ignores any spaces in the filesystemname and mounts """
    split = outputLine.split()
    if (len(split)) == 7:
      device, type, size, used, available, percent, mountpoint = split
      mountinfo = {
        'size': size,
        'used': used,
        'available': available,
        'percent': percent,
        'mountpoint': mountpoint,
        'type': type,
        'device': device}
      return mountinfo
    else:
      return None

  @staticmethod
  @OsFamilyFuncImpl(OsFamilyImpl.DEFAULT)
  def osdisks():
    """ Run df to find out the disks on the host. Only works on linux
    platforms. Note that this parser ignores any filesystems with spaces
    and any mounts with spaces. """
    mounts = []
    df = subprocess.Popen(["df", "-kPT"], stdout=subprocess.PIPE)
    dfdata = df.communicate()[0]
    lines = dfdata.splitlines()
    for l in lines:
      mountinfo = Hardware.extractMountInfo(l)
      if mountinfo != None and Hardware._chk_mount(mountinfo['mountpoint']):
        mounts.append(mountinfo)
      pass
    pass
    return mounts

  @staticmethod
  def _chk_mount(mountpoint):
    if subprocess.call("{0} test -w '{1}'".format(AMBARI_SUDO_BINARY, mountpoint), shell=True) == 0:
      return True
    else:
      return False

  @staticmethod
  @OsFamilyFuncImpl(OSConst.WINSRV_FAMILY)
  def osdisks():
    mounts = []
    runner = shellRunner()
    command_result = runner.runPowershell(script_block=Hardware.WINDOWS_GET_DRIVES_CMD)
    if command_result.exitCode != 0:
      return mounts
    else:
      for drive in [line for line in command_result.output.split(os.linesep) if line != '']:
        available, used, percent, size, type, mountpoint = drive.split(" ")
        mounts.append({"available": available,
                       "used": used,
                       "percent": percent,
                       "size": size,
                       "type": type,
                       "mountpoint": mountpoint})

    return mounts

  def get(self):
    return self.hardware

def main(argv=None):
  hardware = Hardware()
  print hardware.get()

if __name__ == '__main__':
  main()
