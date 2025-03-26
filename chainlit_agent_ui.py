import chainlit as cl
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner, function_tool, handoff, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from pydantic import BaseModel
import asyncio

# Define the order database (mock data)
# In a real-world scenario, this would be replaced with a database query or API call
order_database = {
    "TG12345678": {
        "status": "WaitingToShipping",
        "date": "2025-03-05",
        "items": ["D'alba Piedmont 白松露精華水光噴霧 100毫升", "Eoyunggam 御容鑑 煥顏人蔘再生護膚油 30毫升"],
        "total": 299.99,
        "tracking": "SF1234567890",
        "customer_email": "emily.huang782@outlook.com"
    },
    "TG23456789": {
        "status": "WaittingToPay",
        "date": "2025-03-10",
        "items": ["Unove 深層受損修護髮膜護髮素-溫暖花香 320毫升", "Color Combos 美妝蛋套裝 3件"],
        "total": 2499.99,
        "customer_email": "another@example.com"
    }
}

# Define the function tools for order status and tracking
@function_tool
def check_order_status(order_id: str) -> str:
    """查詢訂單狀態"""
    if order_id in order_database:
        order = order_database[order_id]
        items_list = ", ".join(order['items'])
        return f"訂單編號 {order_id} 目前狀態: {order['status']}，訂單日期: {order['date']}，金額: HK${order['total']}，訂購商品: {items_list}"
    return f"沒有找到訂單 {order_id}"

@function_tool
def get_tracking_info(order_id: str) -> str:
    """查詢物流狀態"""
    if order_id in order_database and order_database[order_id].get("tracking"):
        return f"訂單編號 {order_id} 的物流狀態是: {order_database[order_id]['tracking']}"
    return f"訂單編號 {order_id} 暫無物流資訊或不存在"

# Define the guardrail agent for ecommerce type checking
class EcommerceOutput(BaseModel):
    is_ecommerce_type: bool
    reasoning: str

# Define the guardrail agent
guardrail_agent = Agent(
    name="問題檢查",
    instructions="檢查使用者詢問的是否屬於零售店常見問題",
    output_type=EcommerceOutput,
)

# Define the agents for order, refund, and complaint handling
order_agent = Agent(name="訂單專員", 
handoff_description="專門處理訂單狀態",
instructions="""
您是電子商務平台的訂單查詢專員。您可以協助客戶查詢訂單狀態和物流資訊。
您需要取得訂單號碼才能提供協助。如果客戶沒有提供訂單號，請耐心詢問。
請記住，您的職責只是查詢和提供訂單資訊。如果客戶提出其他需求（如退款或投訴），請向客戶說明您只負責訂單查詢，並建議他們聯絡相關部門。
""",
tools=[check_order_status, get_tracking_info],
model="gpt-4o",
)

# Define the refund agent
refund_agent = Agent(name="退款專員", 
handoff_description="專門處理退款問題",
instructions="""
你是莎莎網店的退款與退換貨專業客服代表。請遵循以下指南：

1. 以友善、專業且有禮貌的態度回應顧客
2. 專門處理退款申請、退換貨流程、退款狀態查詢等相關問題
3. 優先使用中文回應顧客的詢問
4. 清楚說明退款流程和所需時間
5. 提供清晰簡潔的退換貨政策資訊
6. 主動詢問顧客是否還有其他需要協助的事項
7. 協助顧客解決退款與退換貨過程中的疑難

請記住：你的專長是處理退款與退換貨相關問題，確保顧客了解退款流程與狀態。
""",
tools=[check_order_status],
model="gpt-4o",
)

# Define the complaint agent
complaint_agent = Agent(name="客訴專員", 
handoff_description="專門處理客訴問題",                        
instructions="""
你是莎莎網店的客訴處理專業客服代表。請遵循以下指南：

1. 以高度同理心、友善且專業的態度回應顧客
2. 專門處理顧客投訴、商品品質問題、服務體驗不佳等相關問題
3. 優先使用中文回應顧客的詢問
4. 認真傾聽顧客的不滿，並表達真誠的歉意
5. 提供具體的解決方案或賠償政策
6. 主動詢問顧客是否接受解決方案
7. 確保顧客的不滿得到妥善處理

請記住：你的專長是處理顧客投訴問題，將負面體驗轉為正面，挽回顧客的信任。
""",
    tools=[check_order_status],
    model="o3-mini",
)

# Define the handoff functions for each agent
transfer_to_order_specialist = handoff(
    agent=order_agent,
    tool_name_override="transfer_to_order_specialist",
    tool_description_override="當客戶需要查詢訂單狀態或物流資訊時使用此工具。例如：「我想查詢訂單狀態」、「我的包裹到哪了」等情況。"
)

transfer_to_refund_specialist = handoff(
    agent=refund_agent,
    tool_name_override="transfer_to_refund_specialist",
    tool_description_override="當客戶明確要求退款或退貨時使用此工具。例如：「我想申請退款」、「如何退貨」等情況。"
)

transfer_to_complaint_specialist = handoff(
    agent=complaint_agent,
    tool_name_override="transfer_to_complaint_specialist",
    tool_description_override="僅當客戶明確表示不滿、投訴或投訴時使用此工具。例如：「我對服務很不滿」、「我要投訴」等情況。"
)

# Define the guardrail function for ecommerce type checking
async def ecommerce_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(EcommerceOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_ecommerce_type,
    )

# Define the main triage agent
triage_agent = Agent(name="莎莎網店客服", instructions=prompt_with_handoff_instructions("""
您是平台的客服前台。您的工作是了解客戶需求並將他們引導至合適的專業客服。請根據以下明確的指引決定如何處理客戶查詢：

1.訂單查詢類問題：
- 例如：“我想查詢訂單狀態”、“我的包裹什麼時候到”、“能告訴我訂單號XXX的情況嗎”
- 操作：使用transfer_to_order_specialist工具

2.退款類問題：
- 例如：“我想申請退款”、“這個產品有問題，我要退貨”、“如何辦理退款”
- 操作：使用transfer_to_refund_specialist工具

3.投訴類問題：
- 例如：“我對你們的服務很不滿”、“我要投訴”、“這個體驗太糟糕了”
- 操作：使用transfer_to_complaint_specialist工具

4.一般問題：
- 例如：「你們的營業時間是什麼時候」、「如何修改收貨地址」等
- 操作：直接客戶回答

重要規則：
- 請嚴格依照上述分類選擇合適的交接工具
- 不要過度解讀客戶意圖選擇，根據客戶明確表達的需求工具
- 如果不確定，請先詢問更多信息，而不是急於交接
- 首次交流時，除非客戶明確表達了申訴或退款需求，否則應先用order_specialist處理
                                                                                  
"""),
    handoffs=[
        transfer_to_order_specialist, 
        transfer_to_refund_specialist, 
        transfer_to_complaint_specialist
    ],
    input_guardrails=[
        InputGuardrail(guardrail_function=ecommerce_guardrail),
    ],
    model="gpt-3.5-turbo",
)

@cl.on_message
async def on_message(message: cl.Message):
    """處理傳入的用戶訊息"""
    user_input = message.content
    
    # Show a temporary thinking message
    await cl.Message(content="思考中...").send()
    
    try:
        # Run the agent asynchronously
        result = await Runner.run(triage_agent, user_input)
        
        # Extract the content from the result object
        if hasattr(result, 'content'):
            response_content = result.content
        elif hasattr(result, 'text'):
            response_content = result.text
        else:
            response_content = str(result.final_output)
        
        # Send a new message with the response instead of updating
        await cl.Message(content=response_content).send()
        
    except Exception as e:
        # Handle any errors by sending a new message
        await cl.Message(content=f"Error: {str(e)}").send()

@cl.on_chat_start
async def on_chat_start():
    """在新聊天階段開始時執行"""
    # Send a welcome message
    await cl.Message(
        content="您好！我是莎莎網店的線上客服。很高興為您服務，有任何關於商品、訂單、付款或退換貨的問題，都可以向我詢問。"
    ).send()
