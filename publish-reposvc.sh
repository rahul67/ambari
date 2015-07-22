#!/bin/bash - 
#===============================================================================
#
#          FILE: publish-reposvc.sh
# 
#         USAGE: ./publish-reposvc.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Rahul Agarwal (rahul), rahul.agarwal@flipkart.com
#  ORGANIZATION: Flipkart Internet Pvt. Ltd.
#       CREATED: 07/22/15 20:10:56 IST
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
tmpdir=$$
mkdir ${tmpdir}
find . -iname "*.deb" | xargs cp -t ${tmpdir}
cd ${tmpdir}
arg=""
for deb in *.deb; do
    arg="${arg} --debs ${deb}"
done
/usr/bin/reposervice --host repo-svc-app-0001.nm.flipkart.com --port 8080 pub --repo fdp-infra --appkey fdp-infra ${arg}
cd ..
rm -r ${tmpdir}

