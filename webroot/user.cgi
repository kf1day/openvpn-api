#!/bin/sh

NOW="`date +%s`"
RUN="`dirname ${SCRIPT_FILENAME}`"
DIR="`dirname ${RUN}`"
. "${DIR}/vars.conf"
. "${DIR}/http.inc"


do_list() {
	local l f n
	l=`echo status 2 | nc 127.0.0.1 ${ADMIN_PORT} -q1 | sed -ne '/^ROUTING_TABLE,/{s///;s/,/ /;s/,.*//;p}'`
	printf '{'
	while read f; do
		n=`basename $f '.crt'`
		printf \"$n\"':[%s,%s,"%s"],' `openssl x509 -dates -noout -in $f | cut -d'=' -f2 | date -f- +'%s'; echo $l' ' | sed -e 's/ '$n' .*//;s/.* //'`
	done | sed '$s/,$/}/'
}

if [ "${REQUEST_METHOD}" = "GET" ]; then
	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
	ls -1 "${DIR}/cert/"*".crt" | do_list
	exit
fi
err_405
