#!/bin/sh

NOW="`date +%s`"
RUN="`dirname ${SCRIPT_FILENAME}`"
DIR="`dirname ${RUN}`"
. "${DIR}/vars.conf"
. "${DIR}/http.inc"

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


if [ -z "${PATH_INFO}" ] || [ "${PATH_INFO}" = "/" ]; then
	err_400
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
		printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
		if [ "${QUERY_STRING}" = "dl" ]; then
			printf "Content-Disposition: attachment; filename=${CRT_ID}.ovpn\r\n"
		fi
		printf "\r\n"
		do_export "${CRT_ID}"
		exit
	else
		err_404
	fi
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
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
		printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
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
		printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
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
