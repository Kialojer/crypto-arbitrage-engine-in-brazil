import os

from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import requests
import json
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
load_dotenv(override=True)

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def get_crypto_price_brl(symbol: str) -> str:
    """
    ALWAYS use this get_crypto_price_brl to fetch the current price of ANY cryptocurrency across 5 major Brazilian exchanges.
    Input MUST be the base symbol (e.g., 'BTC', 'ETH', 'SOL', 'DOGE').
    Returns a JSON string containing the prices in BRL for UI rendering.
    """
   
    symbol_upper = symbol.upper().strip()
    symbol_lower = symbol.lower().strip()

    results= []
    #mercadobitcoin

    # ۱. Mercado Bitcoin
    try:
        res = requests.get(f"https://api.mercadobitcoin.net/api/v4/tickers?symbols={symbol_upper}-BRL", timeout=5).json()
        price = float(res[0]['last'])
        results.append({"exchange": "Mercado Bitcoin", "price": price, "symbol": symbol_upper})
    except:
        results.append({"exchange": "Mercado Bitcoin", "error": "Not available"})
    
    # ۲. Binance (Brazil Pair)
    try:
        res =  requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_upper}BRL", timeout=5).json()
        price = float(res["price"])
        results.append({"exchange": "Binance", "price": price, "symbol": symbol_upper})
    except:
        results.append({"exchange": "Binance", "error": "Not available"})

    # ۳. NovaDAX
    try:
        res = requests.get(f"https://api.novadax.com/v1/market/ticker?symbol={symbol_upper}_BRL", timeout=5).json()
        price = float(res['data']['lastPrice'])
        results.append({"exchange": "NovaDAX", "price": price, "symbol": symbol_upper})
    except:
        results.append({"exchange": "NovaDAX", "error": "Not available"})

    # ۴. Brasil Bitcoin
    try:
        res = requests.get(f"https://brasilbitcoin.com.br/API/prices/{symbol_upper}", timeout=5).json()
        price = float(res['last'])
        results.append({"exchange": "Brasil Bitcoin", "price": price, "symbol": symbol_upper})
    except:
        results.append({"exchange": "Brasil Bitcoin", "error": "Not available"})

    # ۵. Bitso
    try:
        res = requests.get(f"https://api.bitso.com/v3/ticker/?book={symbol_lower}_brl", timeout=5).json()
        price = float(res['payload']['last'])
        results.append({"exchange": "Bitso", "price": price, "symbol": symbol_upper})
    except:
        results.append({"exchange": "Bitso", "error": "Not available"})

    return json.dumps(results)


tools = [get_crypto_price_brl]
tool_node = ToolNode(tools)

llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
llm_with_tools = llm.bind_tools(tools)

def reasoning_agent_node(state: AgentState):
    """brain for llm that answer the questions whit use tools """

    
    sys_msg = SystemMessage(content="""You are an expert Crypto Arbitrage AI for the Brazilian market.
                            
    When a user asks for a coin price (e.g., 'Solana' or 'SOL'):
    1. Use the get_crypto_price_brl tool to fetch the data.
    2. Analyze the JSON data returned by the tool.
    3. Your final answer MUST include exactly two parts:
       - First, a friendly text that LISTS THE EXACT PRICE for EVERY exchange you checked. After listing them, clearly point out which exchange is the cheapest to buy from.
       - Second, at the very end of your message, output the RAW JSON array from the tool inside a code block labeled ```json so the frontend can render the cards.
    """)
 
    messages_for_llm = [sys_msg] + state["messages"]
    
    print("🧠 Agent is thinking...")
    response = llm_with_tools.invoke(messages_for_llm)
    
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node("Agent", reasoning_agent_node)

builder.add_node("tools", tool_node)

builder.add_edge(START, "Agent")

builder.add_conditional_edges("Agent", tools_condition)
builder.add_edge("tools", "Agent")

app = builder.compile()

if __name__ == "__main__":
  
    test_session_id = str(uuid.uuid4())
    print(f"🔧 Running local test with Thread ID: {test_session_id}")
    
    user_query = "What is the price of Bitcoin now? and which exchange have best rate "
    inputs = {"messages": [HumanMessage(content=user_query)]}
    
    config = {"configurable": {"thread_id": test_session_id}}
    
    result = app.invoke(inputs, config=config)
    
    print("\n" + "="*50)
    print("🤖 Final Answer:")
    print(result["messages"][-1].content)
    print("="*50)