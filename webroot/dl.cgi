#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

do_export() {
	cat "${DIR}/conf/export.conf"

	echo 'key-direction 1'
	echo '<tls-auth>'
	sed -n '/^-----BEGIN OpenVPN Static key V1-----$/,/^-----END OpenVPN Static key V1-----$/p' "${OPENVPN_TA}"
	echo '</tls-auth>'

	echo '<ca>'
	sed -n '/^-----BEGIN CERTIFICATE-----$/,/^-----END CERTIFICATE-----$/p' "${OPENVPN_CA}"
	echo '</ca>'

	echo '<cert>'
	sed -n '/^-----BEGIN CERTIFICATE-----$/,/^-----END CERTIFICATE-----$/p' "$1"
	echo '</cert>'

	echo '<key>'
	sed -n '/^-----BEGIN PRIVATE KEY-----$/,/^-----END PRIVATE KEY-----$/p' "$1"
	echo '</key>'
}


if [ -z "${PATH_INFO}" -o "${PATH_INFO}" = '/' ]; then
	err_405
fi


CERT_ID=`basename "${PATH_INFO}"`
if [ -f "${DIR}/cert/cur."*".${CERT_ID}" ]; then
	printf 'Status: 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n'
	do_export "${DIR}/cert/cur."*".${CERT_ID}"
	exit
fi

err_404