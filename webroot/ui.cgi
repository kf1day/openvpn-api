#!/bin/sh

DIR="${SCRIPT_FILENAME%/webroot/*}"
. "${DIR}/webroot.inc.sh"

if [ "${PATH_INFO}" = '/status' ]; then
	test -z "${GET_TX}" -o -z "${GET_RX}" && err_400
	test ${GET_TX} -lt 0 -o ${GET_RX} -lt 0 -o ${GET_TX} -gt 100 -o ${GET_RX} -gt 100 && err_400

	printf 'Status: 200 OK\r\nContent-Type: image/svg+xml\r\n\r\n'
	cat << EOF
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="none" width="100%" height="100%" viewBox="0 0 100 8">
<path fill="#6c3" d="M0,4L0,2l${GET_TX},0l0,2z"/>
<path fill="#888" d="M0,6L0,4l${GET_RX},0l0,2z"/>
</svg>
EOF
	exit
fi

if [ `dirname "${PATH_INFO}"` = '/edit' ]; then
	CERT_ID="${PATH_INFO##*/}"
	printf 'Status: 200 OK\r\nContent-Type: text/html\r\n\r\n'
	cat << EOF
<!DOCTYPE html>
<html lang="en">
<head>
<title>${CERT_ID} - OpenVPN Admin</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
<h2>OpenVPN Admin: ${CERT_ID}</h2>
<div><a id="a0" href="/ui.cgi/list/">Done</a><a id="a1" href="/cert.cgi/${CERT_ID}">Add new</a></div>
<table id="t0" width="100%" data-id="${CERT_ID}">
<colgroup>
<col width="5%">
<col>
<col width="25%">
<col>
<col>
<col>
</colgroup>
<thead>
<tr>
<th>Cursor</th>
<th></th>
<th>Serial</th>
<th>Start Date</th>
<th>End Date</th>
<th>Revoked</th>
</tr>
</thead>
<tbody>
</tbody>
</table>
</body>
<script type="text/javascript" src="/edit.js"></script>
</html>
EOF
	exit
fi


if [ "${PATH_INFO%/}" = '/list' -o "${PATH_INFO%/}" = '/listall' ]; then
	printf 'Status: 200 OK\r\nContent-Type: text/html\r\n\r\n'
	cat << EOF
<!DOCTYPE html>
<html lang="en">
<head>
<title>OpenVPN Admin</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
<h2>OpenVPN Admin</h2>
<div><a id="a0" href="#new">Add new</a><input id="i0" type="text" placeholder="Filter"></div>
<table id="t0" width="100%">
<colgroup>
<col>
<col>
<col width="25%">
<col>
<col>
<col width="25%">
<col>
<col>
</colgroup>
<thead>
<tr>
<th>Login</th>
<th></th>
<th></th>
<th>IP</th>
<th>Time</th>
<th>TX / RX</th>
<th>Control</th>
<th>Validity</th>
</tr>
</thead>
<tbody>
</tbody>
</table>
</body>
<script type="text/javascript" src="/list.js"></script>
</html>
EOF
	exit
fi

if [ "${PATH_INFO}" = '/conf/' ]; then
	printf 'Status: 200 OK\r\nContent-Type: text/html\r\n\r\n'
	cat << EOF
<!DOCTYPE html>
<html lang="en">
<head>
<title>OpenVPN Admin - Setup</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
<h2>OpenVPN Admin Setup</h2>
<div><a id="a0" href="/ui.cgi/list/">Done</a></div>
<table id="t0" width="100%">
<colgroup>
<col width="25%">
<col>
<col>
</colgroup>
<thead>
<tr>
<th>Parameter</th>
<th>Value</th>
<th>Status</th>
</tr>
</thead>
<tbody>
<tr id="openvpn_config">
<td>Config Path</td>
<td>${OPENVPN_CONFIG}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_ca" class="crit">
<td>Path to CA certificate (from config)</td>
<td>${OPENVPN_CA}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_crl" class="crit">
<td>Path to Certificate Revocation List (from config)</td>
<td>${OPENVPN_CRL}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_ta" class="crit">
<td>Path to OpenVPN static key (from config)</td>
<td>${OPENVPN_TA}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_ccd" class="crit">
<td>Path to Client Config Directory (from config)</td>
<td>${OPENVPN_CCD}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_mgmt" class="crit">
<td>Management Host and Port (from config)</td>
<td>${OPENVPN_MGMT}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_ca_key">
<td>Path to CA key</td>
<td>${OPENVPN_CA_KEY}</td>
<td>Checking...</td>
</tr>
<tr id="openvpn_ca_serial">
<td>Path to CA serial</td>
<td>${OPENVPN_CA_SERIAL}</td>
<td>Checking...</td>
</tr>
<tr id="cert_keysize">
<td>Key type:size</td>
<td>${CERT_KEYSIZE}</td>
<td>Checking...</td>
</tr>
<tr id="cert_subject">
<td>Certificate default subject</td>
<td>${CERT_SUBJECT}</td>
<td>Checking...</td>
</tr>
<tr id="cert_domain">
<td>Certificate subject domain / e-mail domain</td>
<td>${CERT_DOMAIN}</td>
<td>Checking...</td>
</tr>
<tr id="cert_default_days">
<td>Default issuing length (days)</td>
<td>${CERT_DEFAULT_DAYS}</td>
<td>Checking...</td>
</tr>
</tbody>
</table>
</body>
</html>
EOF
  exit
fi

err_404