def is_final_answer(content: str) -> bool:
    """Treat a no-tool message as final unless it clearly asks for missing input."""
    if not content.strip():
        return False
    return not is_clarification_message(content)

def is_clarification_message(content: str, llm) -> bool:
    """Uses the LLM to determine if the message is a question or a final statement."""
    prompt = (
        "Classify the following assistant message as either 'QUESTION' (asking for input) "
        "or 'ANSWER' (providing the final result).\n"
        f"Message: {content}\n"
        "Classification (Reply with only one word):"
    )
    # Use the base llm (without tools) for a fast check
    response = llm.invoke(prompt).content.strip().upper()
    return "QUESTION" in response
