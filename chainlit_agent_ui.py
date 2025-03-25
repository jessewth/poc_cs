import asyncio
import chainlit as cl
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from pydantic import BaseModel
import asyncio

class EcommerceOutput(BaseModel):
    is_ecommerce_type: bool
    reasoning: str

guardrail_agent = Agent(
    name="問題檢查",
    instructions="檢查如果使用者詢問的是屬於電商常見問題",
    output_type=EcommerceOutput,
)

order_agent = Agent(name="訂單客服", instructions="""
你是莎莎網店的訂單專業客服代表。請遵循以下指南：

1. 以友善、專業且有禮貌的態度回應顧客
2. 專門處理訂單查詢、出貨狀態、物流追蹤等相關問題
3. 優先使用中文回應顧客的詢問
4. 避免承諾無法確認的配送時間
5. 提供清晰簡潔的資訊，避免過長或太技術性的回覆
6. 主動詢問顧客是否還有其他需要協助的事項
7. 提供訂單追蹤的相關資訊和解決方案

請記住：你的專長是處理訂單相關問題，讓顧客清楚了解訂單狀態。
""")

refund_agent = Agent(name="退款客服", instructions="""
你是莎莎網店的退款與退換貨專業客服代表。請遵循以下指南：

1. 以友善、專業且有禮貌的態度回應顧客
2. 專門處理退款申請、退換貨流程、退款狀態查詢等相關問題
3. 優先使用中文回應顧客的詢問
4. 清楚說明退款流程和所需時間
5. 提供清晰簡潔的退換貨政策資訊
6. 主動詢問顧客是否還有其他需要協助的事項
7. 協助顧客解決退款與退換貨過程中的疑難

請記住：你的專長是處理退款與退換貨相關問題，確保顧客了解退款流程與狀態。
""")

complaint_agent = Agent(name="客訴專員", instructions="""
你是莎莎網店的客訴處理專業客服代表。請遵循以下指南：

1. 以高度同理心、友善且專業的態度回應顧客
2. 專門處理顧客投訴、商品品質問題、服務體驗不佳等相關問題
3. 優先使用中文回應顧客的詢問
4. 認真傾聽顧客的不滿，並表達真誠的歉意
5. 提供具體的解決方案或賠償政策
6. 主動詢問顧客是否接受解決方案
7. 確保顧客的不滿得到妥善處理

請記住：你的專長是處理顧客投訴問題，將負面體驗轉為正面，挽回顧客的信任。
""")

async def ecommerce_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(EcommerceOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_ecommerce_type,
    )

triage_agent = Agent(name="莎莎網店客服", instructions="""
你是莎莎網店的專業客服代表。請遵循以下指南：

1. 以友善、專業且有禮貌的態度回應顧客
2. 協助解答關於商品、訂單狀態、退換貨政策和付款方式的問題
3. 優先使用中文回應顧客的詢問
4. 避免承諾無法確認的配送時間或活動
5. 若遇到無法解答的問題，請表示會記錄並轉交給專人處理
6. 提供清晰簡潔的資訊，避免過長或太技術性的回覆
7. 主動詢問顧客是否還有其他需要協助的事項
8. 若需要顧客提供個人資料，請說明用途並保證資料安全

請記住：你的目標是有效解決顧客問題，提供優質服務體驗，並展現莎莎網店的專業形象。
""",
    handoffs=[order_agent, refund_agent, complaint_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=ecommerce_guardrail),
    ],
)

# Initialize the agent
#agent = Agent(name="Assistant", instructions="You are a helpful assistant")

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
