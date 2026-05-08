#!/usr/bin/env python3
"""
Morning Briefing — Context-Aware Cron Job
Executa todas as manhãs (8h) com contexto completo da noite/dia anterior.
"""
# Adicionar paths ao sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))
sys.path.insert(0, str(Path(__file__).parent.parent / "knowledge_base" / "contextual_recall"))

from contextual_recall import contextual_recall, format_contextual_facts, detect_domain
from context_switch_optimizer import get_current_topic_summary, load_state

HOME = Path.home()
SCRIPT_DIR = Path(__file__).parent

# Importar get_context do skill
import importlib.util
spec = importlib.util.spec_from_file_location(
    "get_context", 
    HOME / ".hermes" / "skills" / "context-aware-delegation" / "scripts" / "get_context.py"
)
get_context = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_context)


def generate_briefing():
    """Gera o morning briefing completo."""
    
    # 1. Obter contexto das últimas 24h
    sessions = get_context.get_sessions_summary(hours=24)
    recent_context = get_context.get_recent_context(hours=24, limit=40)
    
    # 2. Obter estado dos topics
    topic_state = get_current_topic_summary()
    
    # 3. Detetar domínios activos
    domains_active = []
    topic_words = []
    if isinstance(topic_state, dict) and topic_state.get("topic_words"):
        topic_words = topic_state.get("topic_words", [])
        # Detetar domínios do último tópico
        topic_text = " ".join(topic_words[:30])
        domains_active = detect_domain(topic_text)
    
    # 4. Buscar factos relevantes dos domínios activos
    facts = {}
    if domains_active:
        facts = contextual_recall(" ".join(domains_active), days=3, top_k=3)
    
    # 5. Construir briefing
    briefing = f"""☀️ *Good Morning, Álvaro!*

━━━━━━━━━━━━━━━━━━━━
📊 *CONTEXT SUMMARY (24h)*
━━━━━━━━━━━━━━━━━━━━

{sessions}

━━━━━━━━━━━━━━━━━━━━
🧠 *LAST TOPIC STATE*
━━━━━━━━━━━━━━━━━━━━
• Tópico atual: `{' '.join(topic_words[:15]) if topic_words else 'Nenhum'}`
• Mensagens no tópico: {topic_state.get('message_count', 0) if isinstance(topic_state, dict) else 0}
• Mudanças de tópico: {topic_state.get('switch_count', 0) if isinstance(topic_state, dict) else 0}
• Última atualização: {topic_state.get('last_update', 'nunca') if isinstance(topic_state, dict) else 'nunca'}

━━━━━━━━━━━━━━━━━━━━
🔄 *ACTIVE DOMAINS*
━━━━━━━━━━━━━━━━━━━━
{', '.join(domains_active) if domains_active else 'Nenhum domínio ativo'}

━━━━━━━━━━━━━━━━━━━━
📌 *RECALLED FACTS*
━━━━━━━━━━━━━━━━━━━━
{format_contextual_facts(facts) if facts else 'Sem factos relevantes para recall.'}

━━━━━━━━━━━━━━━━━━━━
📝 *RECENT CONTEXT*
━━━━━━━━━━━━━━━━━━━━
{recent_context[:2000] if recent_context else 'Sem contexto recente.'}

━━━━━━━━━━━━━━━━━━━━

_Generated: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}_
"""
    
    return briefing


if __name__ == "__main__":
    print("=== MORNING BRIEFING ===")
    briefing = generate_briefing()
    print(briefing)
    
    # Guardar para debug
    output_file = HOME / ".hermes" / "cron_output" / "morning_briefing_last.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(briefing)
    print(f"\n[Briefing saved to {output_file}]")
