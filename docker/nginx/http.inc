# Instellingen op http-niveau, gedeeld door prod.conf en dev.conf.

# Rate limit op inlogpogingen per IP-adres (ADR-001). Alleen POST telt; pagina's laden niet.
map $request_method $inlog_sleutel {
    POST    $binary_remote_addr;
    default "";
}
limit_req_zone $inlog_sleutel zone=inloggen:1m rate=30r/m;
limit_req_status 429;
# Een geremd verzoek komt standaard in de foutlog, met de verzoekregel (en dus de code van een
# uitnodiging). Op info valt het onder het niveau van error_log (notice) en blijft het eruit.
limit_req_log_level info;

# Rate limit van de API (ADR-005): 60 aanroepen per minuut per token, met als sleutel de hele
# header. Met alleen de prefix (niet geheim) kon iemand met nep-geheimen het echte token laten
# remmen (AEG-01). Alleen headers in de vorm van een token tellen; de rest remt de grens per IP.
map $http_authorization $api_token_sleutel {
    "~^Bearer blb_[A-Z2-7]{60}$"  $http_authorization;
    default                       "";
}
limit_req_zone $api_token_sleutel zone=api_token:1m rate=60r/m;
limit_req_zone $binary_remote_addr zone=api_ip:1m rate=300r/m;

# De eenmalige code van een uitnodiging komt niet in de toegangslog.
map $request_uri $log_uri {
    ~^/uitnodiging/  /uitnodiging/...;
    default          $request_uri;
}
log_format zonder_code '$remote_addr [$time_local] "$request_method $log_uri" $status $body_bytes_sent';
# access_log staat per server (app.inc, api.inc, prod.conf). Op http-niveau zou de standaardregel
# uit nginx.conf (formaat main, met de volledige URI) blijven meeschrijven.

proxy_set_header Host $host;
# Nginx overschrijft het clientadres; Flask vertrouwt precies één proxy (PROXY_HOPS=1).
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
server_tokens off;
