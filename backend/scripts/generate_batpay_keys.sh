#!/usr/bin/env bash
# Membuat pasangan kunci RSA-2048 untuk integrasi BATPay (SNAP).
#   - private_key_pkcs8.pem  -> isi ke env BATPAY_PRIVATE_KEY (jangan di-commit; *.pem sudah di .gitignore)
#   - public_key.pem         -> unggah/daftarkan di dashboard BATPay (Upload Public Key)
#
# Pakai: bash backend/scripts/generate_batpay_keys.sh [folder_output]
set -euo pipefail
OUT="${1:-./batpay-keys}"
mkdir -p "$OUT"
openssl genrsa -out "$OUT/private_key.pem" 2048 2>/dev/null
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in "$OUT/private_key.pem" -out "$OUT/private_key_pkcs8.pem"
openssl rsa -in "$OUT/private_key.pem" -pubout -out "$OUT/public_key.pem" 2>/dev/null
chmod 600 "$OUT"/private_key*.pem

echo "Kunci dibuat di: $OUT"
echo "  private_key_pkcs8.pem -> BATPAY_PRIVATE_KEY (rahasia)"
echo "  public_key.pem        -> unggah ke dashboard BATPay"
echo
echo "Nilai BATPAY_PRIVATE_KEY satu baris (untuk .env / Coolify):"
awk 'NF {printf "%s\\n", $0}' "$OUT/private_key_pkcs8.pem"
echo
