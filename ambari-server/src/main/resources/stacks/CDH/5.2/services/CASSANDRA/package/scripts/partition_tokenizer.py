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
import sys
import json
import tokentoolv2
import murmur_tokens

randomPartitioner = "org.apache.cassandra.dht.RandomPartitioner"
murmur3Partitioner = "org.apache.cassandra.dht.Murmur3Partitioner"

def getToken(partitioner=None, totalHosts=1, index=0):
    if (partitioner == randomPartitioner):
        token = tokentoolv2.run([totalHosts])[0][index]
    elif (partitioner == murmur3Partitioner):
        token = murmur_tokens.run(totalHosts)[index]
    return token
    
def print_token(token=False):
    if not token:
        token = getToken(partitioner, totalHosts, index)
    print token
    
if __name__ == '__main__':
    if len(sys.argv) > 4:
        partitioner = sys.argv[1]
        totalHosts = int(sys.argv[2])
        index = int(sys.argv[3])
    else:
        print "Usage: ./partition_tokenizer.py <partitioner class> <# of hosts in cassandra cluster> <host index>"
        sys.exit(0)
    getToken(partitioner, totalHosts, index)
    print_token()
    
