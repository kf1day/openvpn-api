#!/bin/sh

NOW=`date +%s`
DIR=`echo ${SCRIPT_FILENAME} | sed 's!/webroot/.*!!'`
. "${DIR}/webroot.inc.sh"

if [ -z "${GET_FORMAT}" ]; then
	F='%s'
else
	F="${GET_FORMAT}"
fi

if [ -z "${GET_DAYS}" ]; then
	D="${CERT_DEFAULT_DAYS}"
else
	D="${GET_DAYS}"
fi


do_list() {
	local f n
	printf '{'
	while read f; do
		n=`basename $f '.crt'`
		printf '"%s":["%s","%s"],' "$n" `openssl x509 -dates -noout -in $f | cut -d'=' -f2 | date -f- +"$F"`
	done | sed 's/,$//'
	printf '}'
}

do_export() {
	cat "${DIR}/conf/export.conf"

	echo "key-direction 1"
	echo "<tls-auth>"
	sed '/^#/d' "${OPENVPN_TA}"
	echo "</tls-auth>"

	echo "<ca>"
	cat "${OPENVPN_CA}"
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

	echo "certificate = ${OPENVPN_CA}"
	echo "private_key = ${OPENVPN_CA_KEY}"

	echo "default_md = sha1"
	echo "default_days = $D"
	echo "default_crl_days = ${CERT_DEFAULT_DAYS}"
}


if [ -z "${PATH_INFO}" ] || [ "${PATH_INFO}" = "/" ]; then
	if [ "${REQUEST_METHOD}" = "GET" ]; then
		printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
		ls -1 "${DIR}/cert/"*".crt" | do_list
		exit
	fi
	err_405
fi


CERT_ID=`basename "${PATH_INFO}"`
if [ -f "${DIR}/cert/${CERT_ID}.key" ]; then
	if [ -f "${DIR}/cert/${CERT_ID}.crt" ]; then
		STATE=0
	else
		STATE=1
	fi
else
	if [ -f "${DIR}/cert/${CERT_ID}.crt" ]; then
		err_500 "${CERT_ID}"
	else
		STATE=2
	fi
fi

if [ "${REQUEST_METHOD}" = "GET" ]; then
	if [ "${STATE}" = "0" ]; then
		printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
		do_export "${CERT_ID}"
		exit
	else
		err_404
	fi
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	if [ "${STATE}" = "0" ]; then
		mv "${DIR}/cert/${CERT_ID}.crt" "${DIR}/cert/${CERT_ID}.${NOW}.bak"
	fi
	if [ "${STATE}" = "2" ]; then
		openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout "${DIR}/cert/${CERT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CERT_ID}@${CERT_DOMAIN}/CN=${CERT_ID}/" -sha512 2> /dev/null | openssl x509 -req -CA "${OPENVPN_CA}" -CAkey "${OPENVPN_CA_KEY}" -CAserial "${OPENVPN_CA_SERIAL}" -out "${DIR}/cert/${CERT_ID}.crt" -days $D -sha512 2> /dev/null
	else
		openssl req -new -key "${DIR}/cert/${CERT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CERT_ID}@${CERT_DOMAIN}/CN=${CERT_ID}/" -sha512 2> /dev/null | openssl x509 -req -CA "${OPENVPN_CA}" -CAkey "${OPENVPN_CA_KEY}" -CAserial "${OPENVPN_CA_SERIAL}" -out "${DIR}/cert/${CERT_ID}.crt" -days $D -sha512 2> /dev/null
	fi
	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
	printf '["%s","%s"]' `openssl x509 -dates -noout -in "${DIR}/cert/${CERT_ID}.crt" | cut -d'=' -f2 | date -f- +"$F"`
	exit
fi

if [ "${REQUEST_METHOD}" = "PUT" ]; then
	if [ "${STATE}" = "2" ]; then
		err_404
	else
		if [ "${STATE}" = "0" ]; then
			openssl_cnf | openssl ca -config "/dev/stdin" -revoke "${DIR}/cert/${CERT_ID}.crt" 2> /dev/null
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${OPENVPN_CRL}" 2> /dev/null
			mv "${DIR}/cert/${CERT_ID}.crt" "${DIR}/cert/${CERT_ID}.${NOW}.bak"
		fi
		mv "${DIR}/cert/${CERT_ID}.key" "${DIR}/cert/${CERT_ID}.${NOW}.key"
		openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout "${DIR}/cert/${CERT_ID}.key" -subj "${CERT_SUBJECT}/emailAddress=${CERT_ID}@${CERT_DOMAIN}/CN=${CERT_ID}/" -sha512 2> /dev/null | openssl x509 -req -CA "${OPENVPN_CA}" -CAkey "${OPENVPN_CA_KEY}" -CAserial "${OPENVPN_CA_SERIAL}" -out "${DIR}/cert/${CERT_ID}.crt" -days $D -sha512 2> /dev/null
		printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
		printf '["%s","%s"]' `openssl x509 -dates -noout -in "${DIR}/cert/${CERT_ID}.crt" | cut -d'=' -f2 | date -f- +"$F"`
		exit
	fi
fi

if [ "${REQUEST_METHOD}" = "DELETE" ]; then
	if [ "${STATE}" = "2" ]; then
		err_404
	else
		if [ "${STATE}" = "0" ]; then
			openssl_cnf | openssl ca -config "/dev/stdin" -revoke "${DIR}/cert/${CERT_ID}.crt" 2> /dev/null
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${OPENVPN_CRL}" 2> /dev/null
			mv "${DIR}/cert/${CERT_ID}.crt" "${DIR}/cert/${CERT_ID}.${NOW}.bak"
		fi
		mv "${DIR}/cert/${CERT_ID}.key" "${DIR}/cert/${CERT_ID}.${NOW}.key"
		printf "Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
		echo "Revoked successfully"
		exit
	fi
fi

err_405
