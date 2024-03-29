#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

do_export() {
	cat "${DIR}/conf/export.conf"

	echo 'key-direction 1'
	echo '<tls-auth>'
	sed -n '/^-----BEGIN OpenVPN Static key V1-----$/,/^-----END OpenVPN Static key V1-----$/p' "${DIR}/data/ta.key"
	echo '</tls-auth>'

	echo '<ca>'
	sed -n '/^-----BEGIN CERTIFICATE-----$/,/^-----END CERTIFICATE-----$/p' "${DIR}/data/ca.crt"
	echo '</ca>'

	echo '<cert>'
	sed -n '/^-----BEGIN CERTIFICATE-----$/,/^-----END CERTIFICATE-----$/p' "$1"
	echo '</cert>'

	echo '<key>'
	sed -n '/^-----BEGIN PRIVATE KEY-----$/,/^-----END PRIVATE KEY-----$/p;/^-----BEGIN ENCRYPTED PRIVATE KEY-----$/,/^-----END ENCRYPTED PRIVATE KEY-----$/p' "$1"
	echo '</key>'
}

CERT_CN="${PATH_INFO#/}"
CERT_CN="${CERT_CN%%/*}"
CERT_ID="${PATH_INFO#/${CERT_CN}}"
CERT_ID="${CERT_ID#/}"

if [ -z "${CERT_CN}" ]; then
	err_400
fi

if [ -z "${CERT_ID}" -a -f "${DIR}/cert/cur.${CERT_CN}" ]; then
	printf 'Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
	if [ "${GET_TYPE}" = 'txt' ]; then
		do_export "${DIR}/cert/cur.${CERT_CN}" | sed 's/$/\r/'
	else
		do_export "${DIR}/cert/cur.${CERT_CN}"
	fi
	exit
else
	if [ -f "${DIR}/cert/pem.0.${CERT_ID}."*".${CERT_CN}" ]; then
		printf 'Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
		if [ "${GET_TYPE}" = 'txt' ]; then
			do_export "${DIR}/cert/pem.0.${CERT_ID}."*".${CERT_CN}" | sed 's/$/\r/'
		else
			do_export "${DIR}/cert/pem.0.${CERT_ID}."*".${CERT_CN}"
		fi
		exit
	fi
fi

err_404
