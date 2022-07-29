#!/bin/sh

DIR="`dirname $0`"

test -d "${DIR}/cert" || mkdir "${DIR}/cert"
test -d "${DIR}/crldb" || ( mkdir "${DIR}/crldb"; : > "${DIR}/crldb/index.txt"; echo "unique_subject = yes" > "${DIR}/crldb/index.txt.attr"; echo "00" > "${DIR}/crldb/number" )
test -f "${DIR}/conf/vars.conf" || cp "${DIR}/conf/vars.conf.sample" "${DIR}/conf/vars.conf"
test -f "${DIR}/conf/export.conf" || cp "${DIR}/conf/export.conf.sample" "${DIR}/conf/export.conf"

exit
if [ -f "${OPENVPN_CONFIG}" -a -r "${OPENVPN_CONFIG}" ]; then
	while read key val ext; do
		case $key in
			ca)
			OPENVPN_CA="$val"
			;;
			crl-verify)
			OPENVPN_CRL="$val"
			;;
			tls-auth)
			OPENVPN_TA="$val"
			;;
			client-config-dir)
			OPENVPN_CCD="$val"
			;;
			management)
			OPENVPN_MGMT="$val $ext"
			;;
		esac
	done
fi