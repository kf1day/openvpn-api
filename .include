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
