# Admin Credentials Setup — SiteTen

## Auth System (dual-layer)

1. **Password bcrypt** — validação contra `admin_password.hash` (prefixo `$2y$`)
2. **RSA key signature** — a private key enviada pelo user é usada para assinar uma mensagem; a public key no servidor verifica

## Setup Completo (de novo)

```bash
# 1. Diretório
cd ~/repos/SiteTen/api/security/

# 2. Gerar par de chaves RSA (sempre ambos juntos)
openssl genrsa 2048 | tee private_key.pem | \
  openssl rsa -pubout -out admin_public.key

# 3. Gerar hash bcrypt da password (PHP usa $2y$)
python3 -c "
import bcrypt
pw = b'AeSm1979@#'
h = bcrypt.hashpw(pw, bcrypt.gensalt(12)).decode()
with open('admin_password.hash', 'w') as f:
    f.write(h.replace('\$2b\$', '\$2y\$'))
"

# 4. Verificar que tudo funciona (antes de enviar ao Álvaro!)
curl -s -X POST http://localhost:8410/api/auth.php \
  -F "password=AeSm1979@#" \
  -F "private_key=@private_key.pem"
# Esperado: {"success":true,"message":"Cadeados Abertos. Bem-vindo."}
```

## Enviar ao Álvaro

**SEMPRE enviar o `private_key.pem`** — é o ficheiro que ele carrega no browser.

**⚠️ O private_key.pem é o que está em `~/repos/SiteTen/api/security/private_key.pem`.**
Não usar chaves de sessões anteriores ou de `/tmp/`.

## Para enviar via Telegram
```bash
# No Telegram, anexar:
MEDIA:/home/alvarobiano/repos/SiteTen/api/security/private_key.pem
```

## Validar antes de confirmar

Se o curl acima responder `Login Bloqueado: A Chave de Segurança não destrava este servidor.`:
- A private key enviada não corresponde à public key no servidor
- Gerar novo par (passos 2-4 acima)
- Testar novamente antes de notificar o Álvaro

## PHP bcrypt vs Python bcrypt

| Library | Prefix |
|---------|--------|
| PHP `password_hash()` | `$2y$` |
| Python `bcrypt` | `$2b$` |

Na conversão Python → PHP, substituir `$2b$` → `$2y$` (ambos são compatíveis em verificação, mas o PHP prefere `$2y$`).
