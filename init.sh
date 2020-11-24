#!/bin/sh

DIR="`dirname $0`"

test -d "${DIR}/cert" || mkdir "${DIR}/cert"
test -d "${DIR}/crldb" || ( mkdir "${DIR}/crldb"; : > "${DIR}/crldb/index.txt"; echo "unique_subject = yes" > "${DIR}/crldb/index.txt.attr"; echo "00" > "${DIR}/crldb/number" )
test -f "${DIR}/vars.conf" || cp "${DIR}/vars.conf.sample" "${DIR}/vars.conf"
test -f "${DIR}/export.conf" || cp "${DIR}/export.conf.sample" "${DIR}/export.conf"
