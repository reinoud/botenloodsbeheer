# Gedeeld door prod.conf en dev.conf: headers, rate limits en doorsturen naar web.

add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "same-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

client_max_body_size 1m;

location ~ ^/(inloggen|uitnodiging) {
    limit_req zone=inloggen burst=20 nodelay;
    proxy_pass http://web:8000;
}

# Foto's van boten tot 10 MB; de applicatie verkleint ze (ADR-008).
location /boten {
    client_max_body_size 10m;
    proxy_pass http://web:8000;
}

location / {
    proxy_pass http://web:8000;
}
