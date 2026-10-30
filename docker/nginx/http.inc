# Instellingen op http-niveau, gedeeld door prod.conf en dev.conf.

# Rate limit op inlogpogingen per IP-adres (ADR-001). Alleen POST telt; pagina's laden niet.
map $request_method $inlog_sleutel {
    POST    $binary_remote_addr;
    default "";
}
limit_req_zone $inlog_sleutel zone=inloggen:1m rate=30r/m;
limit_req_status 429;

# De eenmalige code van een uitnodiging komt niet in de toegangslog.
map $request_uri $log_uri {
    ~^/uitnodiging/  /uitnodiging/...;
    default          $request_uri;
}
log_format zonder_code '$remote_addr [$time_local] "$request_method $log_uri" $status $body_bytes_sent';
access_log /dev/stdout zonder_code;

proxy_set_header Host $host;
# Nginx overschrijft het clientadres; Flask vertrouwt precies één proxy (PROXY_HOPS=1).
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
server_tokens off;
