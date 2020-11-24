#!/bin/sh

NOW="`date +%s`"
DIR="`dirname $0`/.."
. "${DIR}/vars.conf"


do_list() {
	local l f n
	l=`echo status 2 | nc 127.0.0.1 ${ADMIN_PORT} -q1 | sed -ne '/^ROUTING_TABLE,/{s///;s/,/ /;s/,.*//;p}'`
	printf '{'
	while read f; do
		n=`basename $f '.crt'`
		( echo $n; cat $f | openssl x509 -dates -noout | sed 's/.*=//' | xargs -L1 -i -- date -d"{}" +'%s'; echo $l' ' | sed 's/ '$n' .*//;s/.* //' ) | xargs printf '"%s":[%s,%s,"%s"],'
	done | sed '$s/,$/}\n/'
}

do_export() {
	cat "${DIR}/export.conf"

	echo "key-direction 1"
	echo "<tls-auth>"
	sed '/^#/d' "${CA_DIR}/ta.key"
	echo "</tls-auth>"

	echo "<ca>"
	cat "${CA_DIR}/ca.crt"
	echo "</ca>"

	echo "<cert>"
	cat "${DIR}/cert/$1.crt"
	echo "</cert>"

	echo "<key>"
	cat "${DIR}/cert/$1.key"
	echo "</key>"
}

openssl_cnf() {
	echo "[ ca ]"
	echo "default_ca = CA"

	echo "[ CA ]"
	echo "database = ${DIR}/crldb/index.txt"
	echo "crlnumber = ${DIR}/crldb/number"

	echo "certificate = ${CA_DIR}/ca.crt"
	echo "private_key = ${CA_DIR}/ca.key"

	echo "default_md = sha1"
	echo "default_days = ${DEFAULT_DAYS}"
	echo "default_crl_days = 730"
}

err_400() {
	echo "Status: 400 Bad Request"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	echo "Bad Request"
	exit
}
err_404() {
	echo "Status: 404 Not Found"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	echo "Not Found"
	exit
}
err_405() {
	echo "Status: 405 Method Not Allowed"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	echo "Method Not Allowed"
	exit
}
err_409() {
	echo "Status: 409 Conflict"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	echo "Conflict"
	exit
}
err_500() {
	echo "Status: 500 Internal Server Error"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	echo "Error: Missing private key: $1"
	exit
}

if [ -z "${PATH_INFO}" ]; then
	err_400
fi
if [ "${PATH_INFO}" = "/" ]; then
	if [ "${REQUEST_METHOD}" = "GET" ]; then
		echo "Status: 200 OK"
		echo "Content-Type: application/json; charset=utf-8"
		echo
		ls -1 "${DIR}/cert/"*".crt" | do_list
		exit
	fi
	err_405
fi

CRT_ID=`basename "${PATH_INFO}"`
if [ -r "${DIR}/cert/${CRT_ID}.key" ]; then
	if [ -r "${DIR}/cert/${CRT_ID}.crt" ]; then
		STATE=0
	else
		STATE=1
	fi
else
	if [ -r "${DIR}/cert/${CRT_ID}.crt" ]; then
		err_500 "${CRT_ID}"
	else
		STATE=2
	fi
fi

if [ "${REQUEST_METHOD}" = "GET" ]; then
	if [ "${STATE}" = "0" ]; then
		echo "Status: 200 OK"
		echo "Content-Type: text/plain; charset=utf-8"
		if [ "${QUERY_STRING}" = "dl" ]; then
			echo "Content-Disposition: attachment; filename=${CRT_ID}.ovpn"
		fi
		echo
		do_export "${CRT_ID}"
		exit
	else
		err_404
	fi
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	echo "Status: 200 OK"
	echo "Content-Type: text/plain; charset=utf-8"
	echo
	if [ "${STATE}" = "0" ]; then
		mv "${DIR}/cert/${CRT_ID}.crt" "${DIR}/cert/${CRT_ID}.${NOW}.bak"
	fi
	if [ "${STATE}" = "2" ]; then
		openssl req -new -newkey rsa:2048 -nodes -keyout "${DIR}/cert/${CRT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CRT_ID}@${MAIL_DOMAIN}/CN=${CRT_ID}/" -sha512 | openssl x509 -req -CA "${CA_DIR}/ca.crt" -CAkey "${CA_DIR}/ca.key" -CAserial "${CA_DIR}/ca.srl" -out "${DIR}/cert/${CRT_ID}.crt" -days ${DEFAULT_DAYS} -sha512
	else
		openssl req -new -key "${DIR}/cert/${CRT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CRT_ID}@${MAIL_DOMAIN}/CN=${CRT_ID}/" -sha512 | openssl x509 -req -CA "${CA_DIR}/ca.crt" -CAkey "${CA_DIR}/ca.key" -CAserial "${CA_DIR}/ca.srl" -out "${DIR}/cert/${CRT_ID}.crt" -days ${DEFAULT_DAYS} -sha512
	fi
	exit
fi

if [ "${REQUEST_METHOD}" = "PUT" ]; then
	if [ "${STATE}" = "2" ]; then
		err_404
	else
		echo "Status: 200 OK"
		echo "Content-Type: text/plain; charset=utf-8"
		echo
		if [ "${STATE}" = "0" ]; then
			openssl_cnf | openssl ca -config "/dev/stdin" -revoke "${DIR}/cert/${CRT_ID}.crt"
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${CA_DIR}/revoke.crl"
			mv "${DIR}/cert/${CRT_ID}.crt" "${DIR}/cert/${CRT_ID}.${NOW}.bak"
		fi
		mv "${DIR}/cert/${CRT_ID}.key" "${DIR}/cert/${CRT_ID}.${NOW}.key"
		openssl req -new -newkey rsa:2048 -nodes -keyout "${DIR}/cert/${CRT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CRT_ID}@${MAIL_DOMAIN}/CN=${CRT_ID}/" -sha512 | openssl x509 -req -CA "${CA_DIR}/ca.crt" -CAkey "${CA_DIR}/ca.key" -CAserial "${CA_DIR}/ca.srl" -out "${DIR}/cert/${CRT_ID}.crt" -days ${DEFAULT_DAYS} -sha512
		exit
	fi
fi

if [ "${REQUEST_METHOD}" = "DELETE" ]; then
	if [ "${STATE}" = "2" ]; then
		err_404
	else
		echo "Status: 200 OK"
		echo "Content-Type: text/plain; charset=utf-8"
		echo
		if [ "${STATE}" = "0" ]; then
			openssl_cnf | openssl ca -config "/dev/stdin" -revoke "${DIR}/cert/${CRT_ID}.crt"
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${CA_DIR}/revoke.crl"
			mv "${DIR}/cert/${CRT_ID}.crt" "${DIR}/cert/${CRT_ID}.${NOW}.bak"
		fi
		mv "${DIR}/cert/${CRT_ID}.key" "${DIR}/cert/${CRT_ID}.${NOW}.key"
		exit
	fi
fi

err_405
