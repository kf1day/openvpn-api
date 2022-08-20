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

do_config() {
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

do_list() {
	while IFS='.' read a b c d e; do
		printf ',"%s":{"startdate":%d,"enddate":%d,"revoked":%d}' "$e" "$c" "$d" "$b"
	done | sed 's/^,//'
}

head_json() {
	printf 'Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n'
}

CERT_CN="${PATH_INFO#/}"
CERT_CN="${CERT_CN%%/*}"
CERT_ID="${PATH_INFO#/${CERT_CN}}"
CERT_ID="${CERT_ID#/}"


if [ -z "${CERT_CN}" ]; then
	case "${REQUEST_METHOD}" in
	'GET')
		head_json; {
			printf '{'
			find "${DIR}/cert/" -type l -name 'cur.*' -printf '%l\n' | sort -t'.' -k5 | do_list
			printf '}'
		} 2>/dev/null
		;;
	'POST')
		head_json; {
			printf '{'
			find "${DIR}/cert/" -type f -printf '%f\n' | sort -t'.' -k3nr | sort -ust'.' -k5 | do_list
			printf '}'
		} 2>/dev/null
		;;
	*)
		err_405
		;;
	esac
else
	case "${REQUEST_METHOD}" in
	'GET')
		[ `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` -eq 0 ] && err_404
		[ -L "${DIR}/cert/cur.${CERT_CN}" ] && cur=`readlink "${DIR}/cert/cur.${CERT_CN}" | cut -d'.' -f3` || cur=0

		head_json; {
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
		} 2>/dev/null
		;;
	'PUT')
		[ `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` -eq 0 ] && err_404
		head_json
		if [ -z "${CERT_ID}" ]; then
			if [ -L "${DIR}/cert/cur.${CERT_CN}" ]; then
				e=`rm "${DIR}/cert/cur.${CERT_CN}" 2>&1`
				if [ $? -eq 0 ]; then
					printf '{"code":0,"message":"item unchecked"}'
				else
					printf '{"code":2,"message":"%s"}' "$e"
				fi
			else
				printf '{"code":3,"message":"item not checked, nothing to do"}'
			fi
		else
			i=4
			for a in `find "${DIR}/cert/" -type f -name "*.${CERT_ID}.*.${CERT_CN}" -printf '%f\n'`; do
				i=0
				e=`ln -fs "$a" "${DIR}/cert/cur.${CERT_CN}" 2>&1`
				if [ $? -eq 0 ]; then
					printf '{"code":0,"message":"item checked"}'
				else
					printf '{"code":2,"message":"%s"}' "$e"
				fi
				break
			done
			if [ $i -eq 4 ]; then
				printf '{"code":4,"message":"item not found"}'
			fi
		fi
		;;
	'POST')
		head_json

		if [ -n "${CERT_ID}" ]; then
			find "${DIR}/cert/" -type f -name "*.${CERT_ID}.*.${CERT_CN}" -printf '%f\n' | {
				i=4
				while IFS='.' read a b c d e; do
					if [ "$a" = 'rev' -a "$b" -ne 0 ]; then
						if [ -L "${DIR}/cert/cur.$e" -a `readlink "${DIR}/cert/cur.$e"` = "$a.$b.$c.$d.$e" ]; then
							ln -fs "pem.0.$c.$d.$e" "${DIR}/cert/cur.$e"
						fi
						mv "${DIR}/cert/$a.$b.$c.$d.$e" "${DIR}/cert/pem.0.$c.$d.$e"
						i=0
					else
						i=3
					fi
				done
				case "$i" in
					0)
					find "${DIR}/cert/" -type f -name 'rev.*' -printf '%f\n' | sort -t'.' -k2n | do_crl_index
					do_config | openssl ca -config "/dev/stdin" -gencrl -out "${DIR}/data/index.crl" 2> /dev/null
					printf '{"code":0,"message":"item unrevoked"}'
					;;
					3)
					printf '{"code":3,"message":"item not revoked, nothing to do"}'
					;;
					4)
					printf '{"code":4,"message":"item not found"}'
					;;
				esac
			}
			exit
		fi
		TGT="pem.$$"
		e=`{
			openssl req -new -newkey "${CERT_KEYSIZE}" -nodes -keyout /dev/fd/3 -subj "${CERT_SUBJECT}/emailAddress=${CERT_CN}@${CERT_DOMAIN}/CN=${CERT_CN}/" -${CERT_HASH} \
			| openssl x509 -req -CA "${DIR}/data/ca.crt" -CAkey "${DIR}/data/ca.key" -CAserial "${DIR}/data/serial" -days $D -${CERT_HASH} -out "${DIR}/cert/${TGT}"
		} 2>/dev/null 3>&1`


cat << EOF >> "${DIR}/cert/${TGT}"
$e
EOF

		a=`openssl x509 -noout -dates -in "${DIR}/cert/${TGT}" | cut -d'=' -f2 | date -f- +'%s' | xargs echo`
		b="${a#* }"
		a="${a% *}"
		c=`openssl x509 -noout -serial -in "${DIR}/cert/${TGT}"`
		c="${c#*=}"

		mv "${DIR}/cert/${TGT}" "${DIR}/cert/pem.0.$a.$b.${CERT_CN}"
		ln -fs "pem.0.$a.$b.${CERT_CN}" "${DIR}/cert/cur.${CERT_CN}"

		printf '{"code":0,"message":"certificate created","id":%d,"startdate":%d,"enddate":%d,"serial":"%s"}' "$a" "$a" "$b" "$c"
		;;
	'DELETE')
		[ `find "${DIR}/cert/" -type f -name "*.${CERT_CN}" | wc -l` -eq 0 ] && err_404
		[ -z "${CERT_ID}" ] && err_400 'item ID is mandatory'

		head_json
		find "${DIR}/cert/" -type f -name "*.${CERT_ID}.*.${CERT_CN}" -printf '%f\n' | {
			i=4
			f=`date +'%s'`
			while IFS='.' read a b c d e; do
				if [ "$a" = 'pem' -a "$b" -eq 0 ]; then
					if [ -L "${DIR}/cert/cur.$e" -a `readlink "${DIR}/cert/cur.$e"` = "$a.$b.$c.$d.$e" ]; then
						ln -fs "rev.$f.$c.$d.$e" "${DIR}/cert/cur.$e"
					fi
					mv "${DIR}/cert/$a.$b.$c.$d.$e" "${DIR}/cert/rev.$f.$c.$d.$e"
					i=0
				else
					i=3
				fi
			done
			case "$i" in
				0)
				find "${DIR}/cert/" -type f -name 'rev.*' -printf '%f\n' | sort -t'.' -k2n | do_crl_index
				do_config | openssl ca -config "/dev/stdin" -gencrl -out "${DIR}/data/index.crl" 2> /dev/null
				printf '{"code":0,"message":"item revoked","revoked":%d}' "$f"
				;;
				3)
				printf '{"code":3,"message":"item revokation already done, nothing to do"}'
				;;
				4)
				printf '{"code":4,"message":"item not found"}'
				;;
			esac
		}
		;;
	*)
		err_405
		;;
	esac
fi
