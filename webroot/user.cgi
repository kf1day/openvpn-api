#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

do_list() {
	#HEADER,CLIENT_LIST,Common Name,Real Address,Virtual Address,Virtual IPv6 Address,Bytes Received,Bytes Sent,Connected Since,Connected Since (time_t),Username,Client ID,Peer ID
	local cn remote ip ip6 rx tx a tt b id peer
	printf '{'
	while IFS=',' read cn remote ip ip6 rx tx a tt b id peer; do
		if [ -n "$peer" ]; then
			printf ',"%s":{"ip":"%s","remote":"%s","time":%d,"tx":%d,"rx":%d}' "$cn" "$ip" "$remote" "$tt" "$tx" "$rx" 2>/dev/null
		fi
	done | sed 's/^,//'
	printf '}'
}

do_status() {
	local remote ip ips rx tx time user x id peer
	printf '{'
	while IFS=',' read remote ip ips rx tx time user x id peer; do
		printf '"%d":{"ip":"%s","remote":"%s","time":"%s","tx":%d,"rx":%d},' "$id" "$ip" "$remote" `date -d "$time" +"$F"` "$tx" "$rx"
	done | sed 's/,$//'
	printf '}'
}

CERT_ID="${PATH_INFO#/}"
CERT_ID="${CERT_ID%%/*}"
CERT_OP="${PATH_INFO#/${CERT_ID}}"
CERT_OP="${CERT_OP#/}"

if [ -z "${CERT_ID}" ]; then
	if [ "${REQUEST_METHOD}" = 'GET' ]; then
		printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
		echo status 2 | nc ${OPENVPN_MGMT} -q1 | sed -ne '/^CLIENT_LIST,/{s///p}' | do_list
		exit
	fi
	err_405
fi

printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
echo status 2 | nc ${OPENVPN_MGMT} -q1 | sed -ne "/^CLIENT_LIST,${CERT_ID},/{s///;p}" | do_status

#err_405
