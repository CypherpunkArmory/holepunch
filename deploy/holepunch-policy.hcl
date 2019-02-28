# Developers can read and set all secrets
path "secret/holepunch" {
  capabilities = ["read", "list"]
}
