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

def run(nodes = 1):
    tokens = {}
    for i in range(nodes):
        tokens[i] = (((2**64 / 4) * i) - 2**63)        
    return tokens

def print_tokens(tokens=False):
    if not tokens:
        tokens = run(nodes)
    print json.dumps(tokens, sort_keys=True, indent=4)
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        nodes = int(sys.argv[1])
    else:
        print "Usage: ./murmur_tokens.py <nodes in cluster>"
        sys.exit(0)
    run(nodes)
    print_tokens()
    
