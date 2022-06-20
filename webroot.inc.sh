err_400() {
	printf "Status: 400 Bad Request\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
	echo "Bad Request"
	exit
}
err_404() {
	printf "Status: 404 Not Found\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
	echo "Not Found"
	exit
}
err_405() {
	printf "Status: 405 Method Not Allowed\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
	echo "Method Not Allowed"
	exit
}
err_409() {
	printf "Status: 409 Conflict\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
	echo "Conflict"
	exit
}
err_500() {
	printf "Status: 500 Internal Server Error\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
	echo "Error: Missing private key: $1"
	exit
}

. "${DIR}/conf/vars.conf"


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
	done < "${OPENVPN_CONFIG}"
fi

if [ -n "${QUERY_STRING}" ]; then
	QUERY_STRING=`echo $QUERY_STRING | sed 's/&/\n/g'`
	while IFS='=' read key val; do
		key=`echo $key | sed 's/[^A-Za-z0-9]//g;s/.*/\U&/'`
		val=`echo $val | sed 's/%20/ /g;s/%22/"/g'`
		eval GET_$key='$val'
	done << EOF
${QUERY_STRING}
EOF
fi

unset QUERY_STRING key val ext
