#!/usr/bin/env python3
"""
Test Router Agent - Multi-Source Support
"""
from agents.router_agent import router_agent

def test_router():
    """Test if router correctly identifies different query types"""

    test_cases = [
        ("DB Query", "How many users logged in today?", "db"),
        ("DB Query", "Show me all orders from last month", "db"),
        ("Web Query", "What is the weather in Paris?", "web"),
        ("Web Query", "Latest news in artificial intelligence", "web"),
        ("RAG Query", "Explain machine learning from documentation", "rag"),
        ("RAG Query", "What does our product documentation say?", "rag"),
        ("Multi Query", "How many users AND what is the latest AI news?", "multi"),
        ("Multi Query", "Show user statistics and current market trends", "multi"),
        ("Multi Query", "Compare sales data with industry news", "multi"),
    ]

    print("\n" + "="*70)
    print("Testing Router Agent - Multi-Source Support")
    print("="*70 + "\n")

    correct = 0
    total = len(test_cases)

    for label, query, expected in test_cases:
        state = {"query": query, "user_id": "test"}
        result = router_agent(state)
        actual = result.get("route")

        is_correct = actual == expected
        emoji = "✅" if is_correct else "❌"

        if is_correct:
            correct += 1

        print(f"{emoji} {label}:")
        print(f"   Query: \"{query}\"")
        print(f"   Expected: {expected} | Actual: {actual}")
        print()

    print("="*70)
    print(f"Results: {correct}/{total} correct ({100*correct//total}%)")
    print("="*70)

    if correct == total:
        print("\n✅ All routing tests passed!")
        print("\n🎯 Your system SUPPORTS multi-agent from multiple sources!")
        print("\nSupported query types:")
        print("  • Single source (rag, db, web)")
        print("  • Multi-source (combines all three)")
    else:
        print(f"\n⚠️  {total-correct} routing test(s) need improvement")
        print("\nNote: Router behavior depends on LLM interpretation.")
        print("You may need to fine-tune the router prompt for better accuracy.")

if __name__ == "__main__":
    test_router()

