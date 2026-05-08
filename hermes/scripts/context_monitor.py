#!/usr/bin/env python3
"""
Context Monitor — Runs periodically to track topic changes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))
sys.path.insert(0, str(Path(__file__).parent.parent / "knowledge_base" / "contextual_recall"))

from context_switch_optimizer import process, get_current_topic_summary, load_state
from contextual_recall import detect_domain, format_contextual_facts, get_facts_from_messages

HOME = Path.home()


def monitor():
    """Monitoriza e regista mudanças de contexto."""
    state = load_state() or {}
    
    # Verificar se há topic ativo
    current_words = (state.get("current_topic") or {}).get("words", [])
    if not current_words:
        print("No active topic to monitor.")
        return
    
    # Analisar domínio atual
    topic_text = " ".join(current_words[:30])
    domains = detect_domain(topic_text)
    
    # Buscar factos relevantes se houver domínio
    facts = {}
    if domains:
        facts = get_facts_from_messages(domains, days=1, limit=2)
    
    print(f"=== CONTEXT MONITOR ===")
    print(f"Domains: {', '.join(domains) if domains else 'None'}")
    print(f"Topic words: {' '.join(current_words[:15])}")
    print(f"Message count: {state.get('current_topic', {}).get('message_count', 0)}")
    print(f"Switch count: {state.get('switch_count', 0)}")
    if facts:
        print(f"\n{format_contextual_facts(facts)}")


if __name__ == "__main__":
    monitor()
