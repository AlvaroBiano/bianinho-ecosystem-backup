# Duplicate Detection — MD5 Based

## Session Notes (30/04/2026)

**Problema:** Telegram pode enviar o mesmo ficheiro duas vezes (ex: `milionario_consciente.pdf` — duas cópias idênticas, uma de 15:12 e outra de 15:17). Processar duplicados desperdiça quota de API.

**Solução:** Comparar MD5 antes de processar.

```bash
# 1. Ver todos os duplicados na pasta documents
cd ~/.hermes/cache/documents
md5sum doc_*.pdf doc_*.zip doc_*.epub 2>/dev/null | sort | uniq -d -w32

# 2. Comparar dois ficheiros específicos
md5sum ficheiro1.pdf ficheiro2.pdf

# 3. Se igual → mesmo conteúdo → não reprocessar
```

**Resultado real 30/04/2026:**
```
c71f96a413a4c888cc5b8ad27adc779b  doc_99ff976c038e_O_milionário_consciente_transforme_seus_desejos_em_riqueza_pessoal.pdf
c71f96a413a4c888cc5b8ad27adc779b  doc_972bc0169003_O_milionário_consciente_transforme_seus_desejos_em_riqueza_pessoal.pdf
```

Ambos são **100% idênticos** (mesmo hash, mesmo tamanho 2.592.251 bytes). O primeiro já tinha 221 chunks no banco.Confirmado: não é preciso reprocessar.

## Workflow Recommendation

```
1. Receber documento novo
2. Verificar se source já existe no banco (chunk count > 0)
3. Se sim → confirmar que já está processado, não fazer nada
4. Se não sure → calcular MD5 do ficheiro
5. Se MD5 = hash conhecido → skip, informar utilizador
6. Se MD5 novo → processar normalmente
```
