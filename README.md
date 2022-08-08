# POSIX shell-scripted backend/UI for OpenVPN server instance
![openvpn-api](https://user-images.githubusercontent.com/13162764/183392585-377578ab-b68e-4056-980a-507db1fa0f3a.png)

## Summary
OpenVPN-API is a set of pure posix-compatible shell scripts which provides management of client configs and certificates via CGI interface. Development is currently in alpha-stage


## Sample config


### nginx + scgid 
```nginx
server {
    listen 8080 default_server;

    root /var/www/openvpn-api/webroot;

    index index.html;

    location ~* ^(.+\.cgi)($|\/.*) {
        try_files $1 =404;

        scgi_pass unix:/run/scgid/sock;
        scgi_param SCRIPT_FILENAME /var/www/openvpn-api/webroot$1;
        scgi_param PATH_INFO $2;
        include scgi_params;
    }
}
```

### mini-httpd
```
host=0.0.0.0
port=80
user=www-data

nochroot

data_dir=/var/www/openvpn-api/webroot
cgipat=**.cgi
charset=utf-8
```
