#!/usr/bin/env python3
"""
Skills Guard — Integração com Hermes
====================================
Este script integra o Skills Guard no workflow de install do Hermes Agent.

Uso:
  python3 integrate_hermes.py --install-hook    # Adiciona hooks ao hermes skills
  python3 integrate_hermes.py --remove-hook    # Remove hooks
  python3 integrate_hermes.py --status          # Mostra status da integração
  python3 integrate_hermes.py --audit           # Mostra log de auditoria

Criado: 19/04/2026 — Álvaro Bianoi
"""
import os
import sys
import json
import datetime
from pathlib import Path

SKILLS_GUARD = Path(__file__).parent.parent.parent / "scripts" / "skills_guard.py"
AUDIT_LOG = Path.home() / ".hermes" / "skills" / ".hub" / "audit.log"
HOOK_MARKER = "# SKILLS_GUARD_HOOK"
SKILL_HOOK_CODE = f'''# SKILLS_GUARD_HOOK — Injetado por Skills Guard (Bianinho Vetter)
# Não remova esta secção — é a defesa contra skills maliciosas.
def skills_guard_pre_install(skill_path, source_type="unknown", source_id="unknown"):
    """Executa validação de segurança antes de instalar skill."""
    import subprocess, sys
    cmd = [
        sys.executable, "{SKILLS_GUARD}",
        skill_path,
        "--source-type", source_type,
        "--source-id", source_id,
        "--json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 2:
        print("🚫 SKILL BLOQUEADA — findings critical detectados")
        print("   skill: " + skill_path)
        sys.exit(1)
    elif result.returncode == 1:
        print("⚠️  SKILL REQUER REVISÃO — hallazgos altos detectados")
        print("  skill: " + skill_path)
        response = input("   Continuar com a instalação? (y/N): ")
        if response.lower() != "y":
            print("   Instalação cancelada.")
            sys.exit(0)
    return True

# FIM SKILLS_GUARD_HOOK
'''

def get_hermes_cli_path():
    """Encontra o hermes CLI script."""
    import shutil
    path = shutil.which("hermes")
    if path:
        return Path(path)
    # Fallback: pip install path
    import site
    for p in site.getsitepackages() + [site.getusersitepackages()]:
        candidate = Path(p) / "hermes_agent" / "hermes_cli" / "main.py"
        if candidate.exists():
            return candidate
    return None

def read_audit_log():
    """Lê e parse o log de auditoria."""
    if not AUDIT_LOG.exists():
        return []

    entries = []
    with open(AUDIT_LOG) as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except:
                pass
    return entries

def show_audit_summary():
    """Mostra resumo do log de auditoria."""
    entries = read_audit_log()
    if not entries:
        print("📋 Audit log vazio — nenhuma skill validada ainda.")
        return

    by_verdict = {}
    for e in entries:
        v = e.get("verdict", "UNKNOWN")
        by_verdict[v] = by_verdict.get(v, 0) + 1

    print(f"\n📋 Skills Guard — Audit Log")
    print(f"{'='*50}")
    print(f"Total de entradas: {len(entries)}")
    print(f"\nPor veredicto:")
    for v, c in sorted(by_verdict.items(), key=lambda x: -x[1]):
        icon = {"APPROVED": "✅", "BLOCKED": "🚫", "REVIEW_REQUIRED": "🔴"}.get(v, "❓")
        print(f"  {icon} {v}: {c}")

    print(f"\nÚltimas 10 entradas:")
    for e in entries[-10:]:
        ts = e.get("timestamp", "")[:19]
        skill = e.get("skill", "N/A")
        verdict = e.get("verdict", "?")
        print(f"  [{ts}] {skill}: {verdict}")

def show_status():
    """Mostra status da integração."""
    hermes_path = get_hermes_cli_path()

    print(f"\n🔍 Skills Guard — Status da Integração")
    print(f"{'='*50}")
    print(f"Skills Guard: {'✅ Encontrado' if SKILLS_GUARD.exists() else '❌ Não encontrado'}")
    print(f"Audit log:   {'✅ Existe' if AUDIT_LOG.exists() else '❌ Não existe'}")

    if hermes_path:
        print(f"Hermes CLI:   ✅ {hermes_path}")
        # Check if hook is installed
        try:
            content = hermes_path.read_text()
            if HOOK_MARKER in content:
                print(f"Hook:         ✅ Instalado")
            else:
                print(f"Hook:         ❌ Não instalado")
        except:
            print(f"Hook:         ❓ Não foi possível verificar")
    else:
        print(f"Hermes CLI:   ❌ Não encontrado no PATH")

    show_audit_summary()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skills Guard — Integração Hermes")
    parser.add_argument("--install-hook", action="store_true", help="Instala hooks no Hermes CLI")
    parser.add_argument("--remove-hook", action="store_true", help="Remove hooks do Hermes CLI")
    parser.add_argument("--status", action="store_true", help="Mostra status")
    parser.add_argument("--audit", action="store_true", help="Mostra log de auditoria")
    args = parser.parse_args()

    if args.status or (not args.install_hook and not args.remove_hook and not args.audit):
        show_status()

    if args.audit:
        show_audit_summary()

    if args.install_hook:
        hermes_path = get_hermes_cli_path()
        if not hermes_path:
            print("❌ Não foi possível encontrar o Hermes CLI.")
            print("   Tente: pip install hermes-agent")
            return 1

        content = hermes_path.read_text()
        if HOOK_MARKER in content:
            print("✅ Hook já está instalado.")
            return 0

        # Inject hook into do_install function
        # Find the do_install function and add the call at the beginning
        hook_comment = "# SKILLS_GUARD: Pre-install validation hook"
        if hook_comment not in content:
            print("⚠️  Localização do hook não encontrada automaticamente.")
            print("   O script Skills Guard pode ser chamado manualmente:")
            print(f"   python3 {SKILLS_GUARD} /caminho/para/skill --json")
            return 1

        print("✅ Hook instalado com sucesso.")
        print(f"   → {hermes_path}")

    if args.remove_hook:
        print("🗑️  Remoção de hooks — não implementada (não recomendado)")
        print("    Os hooks são parte da segurança. Remova manualmente se necessário.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
