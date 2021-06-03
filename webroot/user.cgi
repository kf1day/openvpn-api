#!/bin/sh

NOW="`date +%s`"
DIR="`echo ${SCRIPT_FILENAME} | sed 's!/webroot/.*!!'`"
. "${DIR}/.include"
. "${DIR}/conf/vars.conf"

if [ -z "${GET_FORMAT}" ]; then
	F='%s'
else
	F="${GET_FORMAT}"
fi

do_list() {
	local l f n
	l="`echo status 2 | nc 127.0.0.1 ${OPENVPN_ADMIN_PORT} -q1 | sed -ne 's/^CLIENT_LIST,//p'`"
	printf '{'
	while read f; do
		n="`basename $f '.crt'`"
		printf '"%s":' "$n"
		echo "$l" | sed -ne 's/^'$n',//p' | do_status
		printf ','
	done | sed 's/,$//'
	printf '}'
}

do_status() {
	local remote ip ips rx tx time user x id peer
	printf '{'
	while IFS=, read remote ip ips rx tx time user x id peer; do
		printf '"%d":{"ip":"%s","remote":"%s","time":"%s","tx":%d,"rx":%d},' "$id" "$ip" "$remote" "`date -d "$time" +"$F"`" "$tx" "$rx"
	done | sed 's/,$//'
	printf '}'
}


if [ -z "${PATH_INFO}" ] || [ "${PATH_INFO}" = "/" ]; then
	if [ "${REQUEST_METHOD}" = "GET" ]; then
		printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
		ls -1 "${DIR}/cert/"*".crt" | do_list
		exit
	fi
	err_405
fi


CERT_ID="`basename "${PATH_INFO}"`"

#HEADER,CLIENT_LIST,Common Name,Real Address,Virtual Address,Virtual IPv6 Address,Bytes Received,Bytes Sent,Connected Since,Connected Since (time_t),Username,Client ID,Peer ID

printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
echo status 2 | nc 127.0.0.1 ${OPENVPN_ADMIN_PORT} -q1 | sed -ne '/^CLIENT_LIST,'"${CERT_ID}"',/{s///;p}' | do_status

#err_405
