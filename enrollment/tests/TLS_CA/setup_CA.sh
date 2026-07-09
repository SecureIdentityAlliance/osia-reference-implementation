#!/bin/sh
openssl genrsa -aes256 -out CA.key -passout pass:secret 2048
openssl req -x509 -new -nodes -key CA.key -sha256 -days 7300 -extensions v3_ca -out CA.pem -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=ca.com" -passin pass:secret

# server
openssl genrsa -aes256 -out server.key -passout pass:secret 2048
openssl req -new -key server.key -out server.csr -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=localhost" -addext "subjectAltName = DNS:localhost" -passin pass:secret
openssl x509 -req -copy_extensions copy -in server.csr -CA CA.pem -CAkey CA.key -CAcreateserial -out server.pem -days 7300 -sha256 -passin pass:secret

# client
openssl genrsa -aes256 -out client.key -passout pass:secret 2048
openssl req -new -key client.key -out client.csr -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=client.com" -addext "subjectAltName = DNS:localhost" -passin pass:secret
openssl x509 -req -copy_extensions copy -in client.csr -CA CA.pem -CAkey CA.key -CAcreateserial -out client.pem -days 7300 -sha256 -passin pass:secret


cat CA.pem server.pem > server-ca.pem
cat CA.pem client.pem > client-ca.pem
openssl rsa -in client.key -passin pass:secret > client.key.clear
