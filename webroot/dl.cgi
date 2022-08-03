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
	sed -n '/^-----BEGIN PRIVATE KEY-----$/,/^-----END PRIVATE KEY-----$/p' "$1"
	echo '</key>'
}

CERT_ID="${PATH_INFO#/}"
CERT_ID="${CERT_ID%%/*}"
CERT_OP="${PATH_INFO#/${CERT_ID}}"
CERT_OP="${CERT_OP#/}"

if [ -z "${CERT_ID}" ]; then
	err_400
fi

if [ -z "${CERT_OP}" -a -f "${DIR}/cert/cur."*".${CERT_ID}" ]; then
	printf 'Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
	do_export "${DIR}/cert/cur."*".${CERT_ID}"
	exit
else
	if [ -f "${DIR}/cert/pem.${CERT_OP}.${CERT_ID}" ]; then
		printf 'Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
		do_export "${DIR}/cert/pem.${CERT_OP}.${CERT_ID}"
		exit
	fi
fi

err_404 
