import os
import requests
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 

load_dotenv(override=True)

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def get_crypto_price_brl(symbol: str) -> str:
    """
    Get the current price of a cryptocurrency in BRL (Brazilian Real) from Mercado Bitcoin.
    Example symbol: 'BTC', 'ETH', 'SOL'.
    """
    url = f"https://api.mercadobitcoin.net/api/v4/tickers?symbols={symbol.upper()}-BRL"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = float(data[0]['last'])
        return f"The current price of {symbol.upper()} is R$ {price:,.2f}"
    except Exception as e:
        return f"Error fetching price for {symbol}: {e}"

@tool
def calculate_tax(amount: float, percentage: float) -> str:
    """
    Calculate the tax or percentage of a given monetary amount.
    Useful for calculating capital gains tax in Brazil.
    """
    tax_value = amount * (percentage / 100)
    return f"{percentage}% tax on R$ {amount:,.2f} is R$ {tax_value:,.2f}"

tools = [get_crypto_price_brl, calculate_tax]

llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
llm_with_tools = llm.bind_tools(tools)

def reasoning_agent_node(state: AgentState):
    """مغز متفکر ایجنت که تصمیم می‌گیرد چه پاسخی بدهد یا چه ابزاری بردارد"""
    
    sys_msg = SystemMessage(content="You are a brilliant financial AI assistant. Use your tools to answer user questions accurately.")
    messages_for_llm = [sys_msg] + state["messages"]
    
    print("🧠 Agent is thinking...")
    response = llm_with_tools.invoke(messages_for_llm)
    
    return {"messages": [response]}

tool_executor_node = ToolNode(tools)

builder = StateGraph(AgentState)
builder.add_node("Agent", reasoning_agent_node)
builder.add_node("tools", tool_executor_node)

builder.add_edge(START, "Agent")
builder.add_conditional_edges("Agent", tools_condition)
builder.add_edge("tools", "Agent")

# 🔴 ۲. ساخت یک نمونه از حافظه
memory = MemorySaver()

# 🔴 ۳. متصل کردن حافظه به گراف در زمان کامپایل
app = builder.compile(checkpointer=memory)

if __name__ == "__main__":
    # 🔴 تولید یک UUID تصادفی و استاندارد برای هر بار اجرای تست
    test_session_id = str(uuid.uuid4())
    print(f"🔧 Running local test with Thread ID: {test_session_id}")
    
    user_query = "What is the price of Bitcoin? Also, if I sell 1 BTC right now, how much is the 15% crypto capital gains tax?"
    inputs = {"messages": [HumanMessage(content=user_query)]}
    
    # استفاده از UUID واقعی در کانفیگ
    config = {"configurable": {"thread_id": test_session_id}}
    
    result = app.invoke(inputs, config=config)
    
    print("\n" + "="*50)
    print("🤖 Final Answer:")
    print(result["messages"][-1].content)
    print("="*50)