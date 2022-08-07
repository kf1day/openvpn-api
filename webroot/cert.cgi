#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

if [ -z "${GET_DAYS}" ]; then
	D="${CERT_DEFAULT_DAYS}"
else
	D="${GET_DAYS}"
fi

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
		find "${DIR}/cert/" -type l -name 'cur.*' -printf '%l\n' | sort -t'.' -k5 | while IFS='.' read a b c d e; do
			printf ',"%s":{"startdate":%d,"enddate":%d,"revoked":%d}' "$e" "$c" "$d" "$b"
		done | sed 's/^,//'
		printf '}'
		exit
	fi
	err_405
fi

if [ "${REQUEST_METHOD}" = 'GET' ]; then
	if [  `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi
	if [ -f "${DIR}/cert/cur.${CERT_CN}" ]; then
		cur=`readlink "${DIR}/cert/cur.${CERT_CN}" | cut -d'.' -f3`
	else
		cur=0
	fi
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	printf '{'

	find "${DIR}/cert/" -type f -name "*.${CERT_CN}" -printf '%f\n' | sort -t'.' -k3n | while IFS='.' read a b c d e; do
		f=`openssl x509 -noout -serial -in "${DIR}/cert/$a.$b.$c.$d.$e"`
		f="${f#*=}"
		if [ "$c" = "$cur" ]; then
			a='true'
		else
			a='false'
		fi
		printf ',"%s":{"startdate":%d,"enddate":%d,"serial":"%s","current":%s,"revoked":%d}' "$c" "$c" "$d" "$f" "$a" "$b"
	done | sed 's/^,//'
	printf '}'
	exit
fi

if [ "${REQUEST_METHOD}" = 'PUT' ]; then
	if [  `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
	if [ -z "${CERT_ID}" ]; then
		find "${DIR}/cert/" -type l -name "cur.${CERT_CN}" -delete
		printf '{"code":0,"message":"Cursor cleared"}'
		exit
	fi
	find "${DIR}/cert/" -type f -name "*.${CERT_ID}.*.${CERT_CN}" -printf '%f\n' | {
		i=0
		while read a; do
			i=$((i+1))
			rm -f "${DIR}/cert/cur.${CERT_CN}"
			ln -s "$a" "${DIR}/cert/cur.${CERT_CN}"
		done
		echo $a
		if [ $i -eq 1 ]; then
			printf '{"code":0,"message":"Cursor is set to given ID"}'
		else
			printf '{"code":4,"message":"Given ID not found"}'
		fi
	}
	exit
fi

if [ "${REQUEST_METHOD}" = "POST" ]; then
	TGT="pem.$$"
	e=`{
		openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout /dev/fd/3 -subj "${CERT_SUBJECT}/emailAddress=${CERT_CN}@${CERT_DOMAIN}/CN=${CERT_CN}/" -${CERT_HASH} \
		| openssl x509 -req -CA "${DIR}/data/ca.crt" -CAkey "${DIR}/data/ca.key" -CAserial "${DIR}/data/serial" -days $D -${CERT_HASH} -out "${DIR}/cert/${TGT}"
	} 2>/dev/null 3>&1`

	cat << EOF >> "${DIR}/cert/${TGT}"
$e
EOF

	a=`openssl x509 -noout -dates -serial -in "${DIR}/cert/${TGT}" | cut -d'=' -f2 | date -f- +'%s' | xargs echo`
	b="${a#* }"
	a="${a% *}"
	c=`openssl x509 -noout -serial -in "${DIR}/cert/${TGT}"`
	c="${c#*=}"

	mv "${DIR}/cert/${TGT}" "${DIR}/cert/pem.0.$a.$b.${CERT_CN}"

	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"

	printf '{"code":0,"message":"Certificate created","id":%d,"startdate":%d,"enddate":%d,"serial":"%s"}' "$a" "$a" "$b" "$c"
	exit
fi

exit

if [ "${REQUEST_METHOD}" = "DELETE" ]; then
	if [  `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` = 0 ];  then
		err_404
	fi	
	if [ -z "${CERT_ID}" ]; then
		err_400 'ID is mandatory'
	fi
	printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
	find "${DIR}/cert/" -type f -name "*.${CERT_ID}.*.${CERT_CN}" -printf '%f\n' | {
		i=4
		f=`date +'%s'`
		while IFS='.' read a b c d e; do
			if [ "$a" = 'pem' -a "$b" -eq 0 ]; then		
				mv "${DIR}/cert/$a.$b.$c.$d.$e" "${DIR}/cert/rev.$f.$c.$d.$e"
				i=0
			else 
				i=3
			fi
		done
		case "$i" in
			1)
			find "${DIR}/cert/" -type f -name 'rev.*' -printf '%f\n' | sort -t'.' -k2n | do_crl_index
			openssl_cnf | openssl ca -config "/dev/stdin" -gencrl -out "${DIR}/data/index.crl" 2> /dev/null
			printf '{"code":0,"message":"Certificate revoked","revoked":%d}' "$f"
			;;
			3)
			printf '{"code":3,"message":"Revokation already done"}'
			;;
			4)
			printf '{"code":4,"message":"Given ID not found"}'
			;;
		esac
	}
	exit
fi

err_405
