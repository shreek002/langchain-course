from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langsmith import traceable
# from groq import Groq

load_dotenv()

MAX_ITERATIONS = 10
MODEL = "qwen3:1.7b"
# MODEL = "llama-3.1-8b-instant"

@tool
def get_product_price(product: str) -> float:
    """Look up the price of a product in the catalog.
    Available products: laptop, headphones, keyboard."""
    normalized_product = product.strip().lower()
    print(f"    >> get_product_price(product='{normalized_product}')")
    prices = {"laptop": 1299.99, "headphones": 149.95, "keyboard": 89.50}
    return prices.get(normalized_product, 0)


@tool
def apply_discount(price: float, discount_tier: str) -> float:
    """Apply a discount tier to a price and return the final price.
    Available tiers: bronze, silver, gold."""
    normalized_tier = discount_tier.strip().lower()
    print(f"    >> apply_discount(price={price}, discount_tier='{normalized_tier}')")
    discount_percentages = {"bronze": 5, "silver": 12, "gold": 23}
    discount = discount_percentages.get(normalized_tier, 0)
    return round(price * (1 - discount / 100), 2)

def is_final_answer(content: str) -> bool:
    return "[NEED_INFO]" not in content

@traceable(name="LangChain Agent Loop Parallel")
def run_agent(question: str):
    tools = [get_product_price, apply_discount]
    tools_by_name = {tool_def.name: tool_def for tool_def in tools}

    llm = init_chat_model(f"ollama:{MODEL}", temperature=0)
    # llm = init_chat_model(f"{MODEL}", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    print(f"Question: {question}")
    print("=" * 60)

    messages = [
        SystemMessage(content=(
                "You are a helpful shopping assistant with two tools: "
                "get_product_price and apply_discount.\n\n"
                "Rules:\n"
                "1. Never guess price. Always call get_product_price.\n"
                "2. Call get_product_price only after you know the product. Never assume missing product.\n"
                "3. Call apply_discount only after get_product_price returns a price.\n"
                "4. Never calculate discount yourself; always use apply_discount.\n"
                "5. If product is missing, ask the user to choose from: laptop, headphones, keyboard.\n"
                "6. If discount tier is missing, ask the user to choose from: bronze, silver, gold.\n"
                "7. If user gives any discount tier text (even invalid), pass it to apply_discount as-is."
                "8. If you need to ask the user for missing info (product or tier), you MUST start your message with [NEED_INFO]."
                "9. If multiple dimensions are missing then ask the user one dimension at a time"
            )),
        HumanMessage(content=question),
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- Iteration {iteration} ---")
        ai_message = llm_with_tools.invoke(messages)
        
        # 1. Add the assistant's message (which contains the tool_calls) to history
        messages.append(ai_message)

        tool_calls = ai_message.tool_calls

        # 2. If no tools are called, handle as final answer or clarification
        if not tool_calls:
            content = (ai_message.content or "").strip()
            if is_final_answer(content):
                print(f"\nFinal Answer: {content}")
                return content
            
            display_text = content.replace("[NEED_INFO]", "").strip()
            print(f"\nAssistant: {display_text}")
            user_follow_up = input("You: ").strip()
            if not user_follow_up: break
            
            messages.append(HumanMessage(content=user_follow_up))
            continue

        # 3. Process ALL tool calls in the current turn
        print(f"[Action] Processing {len(tool_calls)} tool call(s)...")
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id")

            print(f">> Executing {tool_name} with {tool_args}")
            
            tool_to_use = tools_by_name.get(tool_name)
            if tool_to_use:
                observation = tool_to_use.invoke(tool_args)
                messages.append(ToolMessage(
                    content=str(observation), 
                    tool_call_id=tool_call_id
                ))
            else:
                messages.append(ToolMessage(
                    content=f"Error: Tool {tool_name} not found.", 
                    tool_call_id=tool_call_id
                ))

    print("ERROR: Max iterations reached.")
    return None

if __name__ == "__main__":
    print("Hello Simple LangChain Agent")
    print()
    run_agent("What are the prices of products?")

