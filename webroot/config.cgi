#!/bin/sh

DIR=`echo ${SCRIPT_FILENAME} | sed 's!/webroot/.*!!'`
. "${DIR}/webroot.inc.sh"

if [ -n "${GET_TEST}" ]; then
  printf "Status: 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
  case "${GET_TEST}" in
  "openvpn_config")
	if [ -f "${OPENVPN_CONFIG}" ]; then
	  if [ -r "${OPENVPN_CONFIG}" ]; then
        echo '{"status":"ok","message":"Config file readable"}'
	  else
	    echo '{"status":"error","message":"Config file unreadable"}'
	  fi
	else
	  echo '{"status":"error","message":"Config path is not a file"}'
	fi
    ;;
  *)
  	echo '{"status":"error","message":"Unknown test"}'
  esac
  exit
fi

err_400
