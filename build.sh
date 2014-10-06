#!/bin/bash - 
#===============================================================================
#
#          FILE: build.sh
# 
#         USAGE: ./build.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Rahul Agarwal (ragarwal), ragarwal@expedia.com
#  ORGANIZATION: Expedia, Inc.
#       CREATED: 09/25/2014 18:03:39 IST
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
export MAVEN_OPTS=" -Xms512m -Xmx1024m -XX:PermSize=256m -XX:MaxPermSize=512m"
export VERSION=1.7.0.0-shaded
mvn versions:set -DnewVersion=${VERSION}
mvn -B clean install package jdeb:jdeb -DnewVersion=${VERSION} -Drat.numUnapprovedLicenses=1000 -DskipTests
find . -iname "*.deb" | xargs cp -t ~/packages/
