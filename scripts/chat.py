from docchat.chain import RagChat, source_label

SHOW_CHUNKS = True  # set to False to hide the retrieved text


def main():
    chat = RagChat()
    print("Ask about your documents. Type /new to clear memory, exit to quit.")

    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        if question == "/new":
            chat.reset()
            print("History cleared.")
            continue

        result = chat.ask(question)

        if result["standalone"] != question:
            print(f"(searched for: {result['standalone']})")
        print(f"\nAnswer: {result['answer']}\n")

        print("Sources:")
        for i, doc in enumerate(result["docs"], 1):
            print(f"  [{i}] {source_label(doc)}")

        if SHOW_CHUNKS:
            print("\n--- Retrieved text sent to the model ---")
            for i, doc in enumerate(result["docs"], 1):
                print(f"[{i}] {source_label(doc)}\n{doc.page_content[:400]}\n")


if __name__ == "__main__":
    main()