#!/bin/sh

NOW="`date +%s`"
DIR="`echo ${SCRIPT_FILENAME} | sed 's!/webroot/.*!!'`"
. "${DIR}/webroot.inc.sh"

if [ -z "${GET_TX}" ] || [ ${GET_TX} -gt 100 ]; then err_400; fi
if [ -z "${GET_RX}" ] || [ ${GET_RX} -gt 100 ]; then err_400; fi

printf "Status: 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n"

echo '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="none" width="100%" height="100%" viewBox="0 0 100 8">'
echo '<path fill="#6c3" d="M0,4L0,2l'${GET_TX}',0l0,2z"/>'
echo '<path fill="#888" d="M0,6L0,4l'${GET_RX}',0l0,2z"/>'
echo '</svg>'
