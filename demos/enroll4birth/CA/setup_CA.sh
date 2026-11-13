#!/bin/sh
openssl req -x509 -new -noenc -keyout CA.key -out CA.pem -sha256 -days 7300 -extensions v3_ca -addext 'keyUsage=critical,keyCertSign,cRLSign' -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=ca.com"

# server
openssl req -new -noenc -keyout server.key -out server.csr -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=localhost" -addext "subjectAltName = DNS:localhost"
openssl x509 -req -copy_extensions copy -in server.csr -CA CA.pem -CAkey CA.key -CAcreateserial -out server.pem -days 7300 -sha256
rm server.csr

# client
openssl req -new -noenc -keyout client.key -out client.csr -subj "/C=FR/ST=IDF/L=Paris/O=Company/CN=client.com" -addext "subjectAltName = DNS:localhost"
openssl x509 -req -copy_extensions copy -in client.csr -CA CA.pem -CAkey CA.key -CAcreateserial -out client.pem -days 7300 -sha256
rm client.csr

cat client.pem client.key > client-all.pem
cat CA.pem server.pem > server-ca.pem
cat CA.pem client.pem > client-ca.pem
