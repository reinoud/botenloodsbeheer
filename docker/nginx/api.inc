# Interne server voor de API (ADR-005, ADR-012). Niet gepubliceerd: alleen bereikbaar vanaf de
# netwerken van nginx, zoals koppeling. Stuurt alleen /api/v1/ door naar de dienst api.
# Geen eigen proxy_set_header hier, anders vervalt de overschreven X-Forwarded-For uit http.inc.
server {
    listen 8081;
    client_max_body_size 1m;
    access_log /dev/stdout zonder_code;
    add_header X-Content-Type-Options "nosniff" always;

    location /api/v1/ {
        limit_req zone=api_ip burst=50 nodelay;
        limit_req zone=api_token burst=10 nodelay;
        error_page 429 = @te_veel;
        proxy_pass http://api:8000;
    }

    location @te_veel {
        default_type application/json;
        # De grens is 1 aanroep per seconde (60 per minuut); na 1 seconde mag er weer één.
        add_header Retry-After 1 always;
        add_header X-Content-Type-Options "nosniff" always;
        return 429 '{"fout": "Te veel aanroepen."}';
    }

    location / {
        return 404;
    }
}
