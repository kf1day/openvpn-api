#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

if [ -z "${GET_DAYS}" ]; then
	D="${CERT_DEFAULT_DAYS}"
else
	D="${GET_DAYS}"
fi

do_join() {
	local a b c d
	sort | {
		while IFS='	' read a b; do
			if [ "$a" != "$c" ]; then
				[ -n "$d" ] && echo "$d"
				c="$a"
				d="$a"
			fi
			[ -n "$b" ] && d="$d\t$b"
		done
		echo "$d"
	}
}

do_crl_index() {
	local a b c d i
	i=0
	while read a; do
		b=${a#rev.}
		printf '%s\t' ${b%%.*}
		openssl x509 -noout -nameopt compat -enddate -serial -subject -in "${DIR}/cert/$a" | { while IFS='=' read a b; do printf '%s\t' "$b"; done; printf '\n'; }
	done | {
		while IFS='	' read a b c d; do
			i=$((i+1))
			a=`date -d@"$a" +'%y%m%d%H%M%SZ'`
			b=`date -d"$b" +'%y%m%d%H%M%SZ'`
			printf 'R\t%s\t%s\t%s\t%s\t%s\n' "$b" "$a" "$c" 'unknown' "$d"
		done > "${DIR}/data/index.txt"
		printf '00%X\n' "$i" | tail -c3 > "${DIR}/data/number"
	}
}

openssl_cnf() {
	cat << EOF
[ ca ]
default_ca = CA

[ CA ]
database = ${DIR}/data/index.txt
crlnumber = ${DIR}/data/number

certificate = ${DIR}/data/ca.crt
private_key = ${DIR}/data/ca.key

default_md = sha1
default_days = $D
default_crl_days = ${CERT_DEFAULT_DAYS}
EOF
}

CERT_CN="${PATH_INFO#/}"
CERT_CN="${CERT_CN%%/*}"
CERT_ID="${PATH_INFO#/${CERT_CN}}"
CERT_ID="${CERT_ID#/}"


if [ -z "${CERT_CN}" ]; then
	if [ "${REQUEST_METHOD}" = 'GET' ]; then
		printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
		printf '{'
		find "${DIR}/cert/" -type l -printf '%l\t%P\n' | do_join | sort -t'.' -k3 | while IFS='	' read a b c; do
			if [ "${b%%.*}" = 'cur' ]; then
				a="${b#cur.}"
				b="${a#*.}"
				a="${a%%.*}"
				if [ "${c%%.*}" = 'rev' ]; then
					c="${c#rev.}"
					c="${c%%.*}"
				else
					c=0
				fi
				printf ',"%s":{"enddate":%d,"revoked":%d}' "$b" "$a" "$c"
			fi
		done | sed 's/^,//'
		printf '}'
		exit
	fi
	err_405
fi

if [ "${REQUEST_METHOD}" = 'GET' ]; then
	if [  `find "${DIR}/cert/" -type f -name "pem.*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	printf '{'
	{
		find "${DIR}/cert/" -type l -name "*.${CERT_CN}" -printf '%l\t%P\n'
		find "${DIR}/cert/" -type f -name "pem.*.${CERT_CN}" -printf '%P\n'
	} | do_join | while IFS='	' read a b c; do
		[ "${b%%.*}" = 'cur' -o "${c%%.*}" = 'cur' ] && d='true' || d='false'
		[ "${c%%.*}" = 'rev' ] && b="$c"
		if [ "${b%%.*}" = 'rev' ]; then
			b="${b#rev.}"
			b="${b%%.*}"
		else
			b=0
		fi
		c="${a#pem.}"
		c="${c%%.*}"
		openssl x509 -noout -dates -serial -in "${DIR}/cert/$a" | while IFS='=' read a b; do printf '%s\t' "$b"; done
		printf '%d\t%d\t%s\n' $b $c $d
	done | while IFS='	' read a b c d e f; do
		a=`date -d "$a" +'%s'`
		b=`date -d "$b" +'%s'`
		printf ',"%s":{"startdate":%d,"enddate":%d,"serial":"%s","current":%s,"revoked":%d}' "$e" "$a" "$b" "$c" "$f" "$d"
	done | sed 's/^,//'
	printf '}'
	exit
fi

if [ "${REQUEST_METHOD}" = 'PUT' ]; then
	if [  `find "${DIR}/cert/" -type f -name "pem.*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	if [ -z "${CERT_ID}" ]; then
		find "${DIR}/cert/" -type l -name "cur.*.${CERT_CN}" -delete
		printf '{"code":0,"message":"Cursor cleared"}'
		exit
	fi
	if [ -f "${DIR}/cert/pem.${CERT_ID}.${CERT_CN}" ]; then
		find "${DIR}/cert/" -type l -name "cur.*.${CERT_CN}" -delete
		d=`openssl x509 -enddate -noout -in "${DIR}/cert/pem.${CERT_ID}.${CERT_CN}" | cut -d'=' -f2 | date -f- +'%s'`
		ln -s "pem.${CERT_ID}.${CERT_CN}" "${DIR}/cert/cur.$d.${CERT_CN}"
		printf '{"code":0,"message":"Cursor is set to given ID"}'
	else
		printf '{"code":4,"message":"Given ID not found"}'
	fi
	exit
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout "${DIR}/cert/tmp.${NOW}.${CERT_CN}" -subj "${CERT_SUBJECT}/emailAddress=${CERT_CN}@${CERT_DOMAIN}/CN=${CERT_CN}/" -sha512 2> /dev/null | openssl x509 -req -CA "${DIR}/data/ca.crt" -CAkey "${DIR}/data/ca.key" -CAserial "${DIR}/data/serial" -out "${DIR}/cert/pem.${NOW}.${CERT_CN}" -days $D -sha512
	cat "${DIR}/cert/tmp.${NOW}.${CERT_CN}" >> "${DIR}/cert/pem.${NOW}.${CERT_CN}"
	rm "${DIR}/cert/tmp.${NOW}.${CERT_CN}"
	test -f "${DIR}/cert/cur."*".${CERT_CN}" && rm "${DIR}/cert/cur."*".${CERT_CN}"
	e=`openssl x509 -enddate -noout -in "${DIR}/cert/pem.${NOW}.${CERT_CN}" | cut -d'=' -f2 | date -f- +'%s'`

	ln -s "pem.${NOW}.${CERT_CN}" "${DIR}/cert/cur.$e.${CERT_CN}"

	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"

	printf '{"code":0,"message":"Certificate created","id":%d,"startdate":%d,"enddate":%d,"serial":"%s","current":"true"}' "${NOW}" "${NOW}" "$e" `openssl x509 -serial -noout -in "${DIR}/cert/pem.${NOW}.${CERT_CN}" | cut -d'=' -f2`
	exit
fi

if [ "${REQUEST_METHOD}" = "DELETE" ]; then
	if [  `find "${DIR}/cert/" -type f -name "pem.*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi
	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
	if [ -z "${CERT_ID}" ]; then
		printf '{"code":3,"message":"ID is mandatory"}'
		exit
	fi
	if [ -f "${DIR}/cert/pem.${CERT_ID}.${CERT_CN}" ]; then
		if [ `find "$DIR/cert/" -type l -name "rev.*.${CERT_CN}" -printf '%l\n' | grep -c "pem.${CERT_ID}.${CERT_CN}"` = "0" ]; then
			ln -s "pem.${CERT_ID}.${CERT_CN}" "${DIR}/cert/rev.${NOW}.${CERT_CN}"
			find "${DIR}/cert/" -type l -name 'rev.*' -printf '%P\n' | sort -t'.' -k2n | do_crl_index
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${DIR}/data/index.crl" 2> /dev/null
			printf '{"code":0,"message":"Certificate revoked"}' 
		else
			printf '{"code":3,"message":"Revokation already done"}'
		fi
	else
		printf '{"code":4,"message":"Given ID not found"}'
	fi
	exit
fi

err_405
