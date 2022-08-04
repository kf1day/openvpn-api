#!/bin/sh

DIR=`realpath "$0"`
DIR=`dirname "${DIR}"`'/cert'
test "${USER}" = 'root' && WRK="/run/tmp.$$" || WRK="${DIR}/tmp.$$"


test -d "${DIR}" || exit
mkdir -p "${WRK}" || exit

if [ -n "$1" -a -f "$1" ]; then
	find "${DIR}" -name 'rev.*' -delete

	echo 'Indexing cert serials...'
	find "${DIR}" -name 'pem.*' -printf '%P\n' | while read a; do
		e=`openssl x509 -noout -serial -in "${DIR}/$a" | cut -d'=' -f2`
		ln -s "$a" "${WRK}/ser.$e"
	done
	echo 'Done!'

	echo 'Cheking given revokation list...'

	while IFS='	' read r a b s u c; do
		echo "Processing ${WRK}/ser.$s ..."
		if [ -L "${WRK}/ser.$s" ]; then
			b=`echo $b | sed 's/\(..\)\(..\)\(..\)\(..\)\(..\)\(..\)Z/20\1-\2-\3 \4:\5:\6/' | date -f- +'%s'`
			u=`readlink "${WRK}/ser.$s"`
			r="${u#pem.}"
			r="${r#*.}"
			printf 'MARK as REVOKED: %s %s\n' "$s" "$r"
			ln -s "$u" "${DIR}/rev.$b.$r"
		fi
	done < "$1"
	echo 'Done!'
	rm -rf "${WRK}"
	exit
fi

tar -C"${DIR}" -cz . -f "${DIR%cert}bakup."`date +'%s'`'.tgz'

ls -1 "${DIR}/"*'.key' | while read f; do
    mod=`openssl rsa -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    ln -s "$f" "${WRK}/mod.$mod"
done

ls -1 "${DIR}/"*'.crt' | while read f; do
    mod=`openssl x509 -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    if [ -r "${WRK}/mod.$mod" ]; then
        id=`basename "$f" '.crt'`
        echo "$id"
        echo 'Mark as CURRENT'
        datex=`openssl x509 -startdate -noout -in "$f" | sed 's/^notBefore=//' | date -f- +'%s'`
        datez=`openssl x509 -enddate -noout -in "$f" | sed 's/^notAfter=//' | date -f- +'%s'`
        cat "$f" "${WRK}/mod.$mod" > "${DIR}/pem.$datex.$id"
        ln -s "pem.$datex.$id" "${DIR}/cur.$datez.$id"
    fi
done

ls -1 "${DIR}/"*'.bak' | while read f; do
    mod=`openssl x509 -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    if [ -r "${WRK}/mod.$mod" ]; then
        id=`basename "$f" '.bak' | sed 's/\.[0-9]\+$//'`
        echo "$id"
        datex=`openssl x509 -startdate -noout -in "$f" | sed 's/^notBefore=//' | date -f- +'%s'`
        cat "$f" "${WRK}/mod.$mod" > "${DIR}/pem.$datex.$id"
        r="${f%.bak}.key"
        if [ -r "$r" ]; then
            rp=`echo $r | sed 's/.*\.\([0-9]\+\)\.key$/\1/'`
            echo 'Mark as REVOKED'
            ln -s "pem.$datex.$id" "${DIR}/rev.$rp.$id"
        fi
    fi
done

rm -rf "${WRK}"
rm "${DIR}/"*'.key' "${DIR}/"*'.crt' "${DIR}/"*'.bak'

