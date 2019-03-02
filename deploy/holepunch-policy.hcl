# Developers can read and set all secrets
path "secret/holepunch" {
  capabilities = ["read", "list"]
}

path "secret/fabio/certs/api.holepunch.io" {
  capabilities = ["read"]
}
