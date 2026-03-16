from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from .graph import build_workflow
from .state_types import State


def main() -> None:
    workflow = build_workflow()

    config = {
        "configurable": {"thread_id": "demo-cli-thread"},
        "recursion_limit": 100,
    }

    bootstrap_state: State = {
        "passages": [],
        "iteration": 0,
    }

    print("Type 'exit' or press Enter on an empty line to quit.")
    first_turn = True

    while True:
        try:
            user_query = input("query: ").strip()
        except EOFError:
            print()
            break

        if not user_query or user_query.lower() in {"exit", "quit"}:
            break

        turn_input: State = {"messages": [HumanMessage(content=user_query)]}
        if first_turn:
            turn_input = {**bootstrap_state, **turn_input}
            first_turn = False

        result = workflow.invoke(turn_input, config=config)

        messages = result.get("messages", [])
        if messages and isinstance(messages[-1], AIMessage):
            print("answer:", messages[-1].content)
        else:
            print("answer: [no AI message produced]")


if __name__ == "__main__":
    main()
