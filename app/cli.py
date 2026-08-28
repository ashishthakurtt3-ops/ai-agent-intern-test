import argparse
import logging

from .agent import SupportAgent
from .config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Aster & Row support agent")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s %(message)s")
    agent = SupportAgent(get_settings())
    print("Aster & Row Support Agent. Type 'exit' to quit.")
    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message.lower() in {"exit", "quit"}:
            break
        result = agent.answer(message)
        print(f"\nAgent: {result['answer']}")
        if result["handoff"]:
            print("[Human support recommended]")


if __name__ == "__main__":
    main()
