#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

if [ -z "${GET_DAYS}" ]; then
	D="${CERT_DEFAULT_DAYS}"
else
	D="${GET_DAYS}"
fi

do_opts() {
	local a b c
    c=0
    printf '{'
	while IFS='	' read a b; do
        if [ "$a" = "$c" ]; then
            if [ -n "$b" ]; then
                case "${b%%.*}" in
                    'rev')
                        printf ',"revoked":%d' `echo "$a" | cut -d'.' -f2`
                        ;;
                    'cur')
                        printf ',"current":"true"'
                        ;;
                esac
            fi
        else
            c="$a"
			a=${a#pem.}
            printf '},"%s":{"startdate":%d,"enddate":%d' "${a%%.*}" `openssl x509 -dates -noout -in "${DIR}/cert/$c" | cut -d'=' -f2 | date -f- +'%s'`
			printf ',"serial":"%s"' `openssl x509 -serial -noout -in "${DIR}/cert/$c" | cut -d'=' -f2`
        fi
    done | sed 's/^},//;s/$/}/'
    printf '}'
}

openssl_cnf() {
	cat << EOF
[ ca ]
default_ca = CA

[ CA ]
database = ${DIR}/crldb/index.txt
crlnumber = ${DIR}/crldb/number

certificate = ${DIR}/data/ca.crt
private_key = ${DIR}/data/ca.key

default_md = sha1
default_days = $D
default_crl_days = ${CERT_DEFAULT_DAYS}
EOF
}

CERT_ID="${PATH_INFO#/}"
CERT_ID="${CERT_ID%%/*}"
CERT_OP="${PATH_INFO#/${CERT_ID}}"
CERT_OP="${CERT_OP#/}"


if [ -z "${CERT_ID}" ]; then
	if [ "${REQUEST_METHOD}" = 'GET' ]; then
		printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'

		printf '{'
		find "${DIR}/cert/" -name "cur.*" -printf '%P\n' | sort -t'.' -k3 | while IFS='.' read a b c; do printf '"%s":{"enddate":%d},' "$c" "$b"; done | sed 's/,$//'
		printf '}'
		exit
	fi
	err_405
fi

if [ "${REQUEST_METHOD}" = 'GET' ]; then
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	{
		find "${DIR}/cert/" -type l -name "rev.*.${CERT_ID}" -printf '%l\t%P\n'
		find "${DIR}/cert/" -type l -name "cur.*.${CERT_ID}" -printf '%l\t%P\n'
		find "${DIR}/cert/" -name "pem.*.${CERT_ID}" -printf '%P\n'
	} | sort | do_opts
	exit
fi

if [ "${REQUEST_METHOD}" = 'PUT' ]; then
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	if [ -z "${CERT_OP}" ]; then
		find "${DIR}/cert/" -type l -name "cur.*.${CERT_ID}" -delete
		printf '{"code":0,"message":"Cursor cleared"}'
		exit
	fi
	if [ -f "${DIR}/cert/pem.${CERT_OP}.${CERT_ID}" ]; then
		find "${DIR}/cert/" -type l -name "cur.*.${CERT_ID}" -delete
		d=`openssl x509 -enddate -noout -in "${DIR}/cert/pem.${CERT_OP}.${CERT_ID}" | cut -d'=' -f2 | date -f- +'%s'`
		ln -s "pem.${CERT_OP}.${CERT_ID}" "${DIR}/cert/cur.$d.${CERT_ID}"
		printf '{"code":0,"message":"Cursor is set to given index"}'
	else
		printf '{"code":4,"message":"Given index not found"}'
	fi
	exit
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout "${DIR}/cert/tmp.${NOW}.${CERT_ID}" -subj "${CERT_SUBJECT}/emailAddress=${CERT_ID}@${CERT_DOMAIN}/CN=${CERT_ID}/" -sha512 2> /dev/null | openssl x509 -req -CA "${DIR}/data/ca.crt" -CAkey "${DIR}/data/ca.key" -CAserial "${DIR}/data/serial" -out "${DIR}/cert/pem.${NOW}.${CERT_ID}" -days $D -sha512
	cat "${DIR}/cert/tmp.${NOW}.${CERT_ID}" >> "${DIR}/cert/pem.${NOW}.${CERT_ID}"
	rm "${DIR}/cert/tmp.${NOW}.${CERT_ID}"
	test -f "${DIR}/cert/cur."*".${CERT_ID}" && rm "${DIR}/cert/cur."*".${CERT_ID}"
	e=`openssl x509 -enddate -noout -in "${DIR}/cert/pem.${NOW}.${CERT_ID}" | cut -d'=' -f2 | date -f- +'%s'`

	ln -s "pem.${NOW}.${CERT_ID}" "${DIR}/cert/cur.$e.${CERT_ID}"

	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"

	printf '{"code":0,"message":"Certificate created","id":%d,"startdate":%d,"enddate":%d,"serial":"%s","current":"true"}' "${NOW}" "${NOW}" "$e" `openssl x509 -serial -noout -in "${DIR}/cert/pem.${NOW}.${CERT_ID}" | cut -d'=' -f2`
	exit
fi

if [ "${REQUEST_METHOD}" = "DELETE" ]; then
	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
	if [ -z "${CERT_OP}" ]; then
		printf '{"code":3,"message":"Index is mandatory"}'
		exit
	fi
	if [ -f "${DIR}/cert/pem.${CERT_OP}.${CERT_ID}" ]; then
		ln -s "pem.${CERT_OP}.${CERT_ID}" "${DIR}/cert/rev.${NOW}.${CERT_ID}"
		find "${DIR}/cert/" -type l -name "rev.*" -printf '%l\t%P\n' | sort
	else
		printf '{"code":4,"message":"Given index not found"}'
	fi
fi

err_405
