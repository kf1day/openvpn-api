#!/bin/sh

DIR=`realpath "$0"`
DIR=`dirname "${DIR}"`'/cert'
test "${USER}" = 'root' && TMP="/run/tmp.$$" || TMP="${DIR}/tmp.$$"


test -d "${DIR}" || exit
mkdir -p "${TMP}" || exit

tar -C"${DIR}" -cz . -f "${DIR%cert}bakup."`date +'%s'`'.tgz'

ls -1 "${DIR}/"*'.key' | while read f; do
    mod=`openssl rsa -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    ln -s "$f" "${TMP}/mod.$mod"
done

ls -1 "${DIR}/"*'.crt' | while read f; do
    mod=`openssl x509 -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    if [ -r "${TMP}/mod.$mod" ]; then
        id=`basename "$f" '.crt'`
        echo "$id"
        echo 'Mark as CURRENT'
        datex=`openssl x509 -startdate -noout -in "$f" | sed 's/^notBefore=//' | date -f- +'%s'`
        datez=`openssl x509 -enddate -noout -in "$f" | sed 's/^notAfter=//' | date -f- +'%s'`
        cat "$f" "${TMP}/mod.$mod" > "${DIR}/pem.$datex.$id"
        ln -s "pem.$datex.$id" "${DIR}/cur.$datez.$id"
    fi
done

ls -1 "${DIR}/"*'.bak' | while read f; do
    mod=`openssl x509 -modulus -noout -in "$f" | sha256sum | cut -d' ' -f1`
    if [ -r "${TMP}/mod.$mod" ]; then
        id=`basename "$f" '.bak' | sed 's/\.[0-9]\+$//'`
        echo "$id"
        datex=`openssl x509 -startdate -noout -in "$f" | sed 's/^notBefore=//' | date -f- +'%s'`
        cat "$f" "${TMP}/mod.$mod" > "${DIR}/pem.$datex.$id"
        r="${f%.bak}.key"
        if [ -r "$r" ]; then
            rp=`echo $r | sed 's/.*\.\([0-9]\+\)\.key$/\1/'`
            echo 'Mark as REVOKED'
            ln -s "pem.$datex.$id" "${DIR}/rev.$rp.$id"
        fi
    fi
done

rm -rf "${TMP}"
rm "${DIR}/"*'.key' "${DIR}/"*'.crt' "${DIR}/"*'.bak'

