from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import boto3

app = Flask(__name__)

# ตั้งค่า Token
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # เชื่อมต่อกับ Bedrock Agent
    response = client.invoke_agent(
        agentId=os.getenv('BEDROCK_AGENT_ID'),
        agentAliasId=os.getenv('BEDROCK_AGENT_ALIAS_ID'),
        sessionId=event.source.user_id,
        inputText=event.message.text
    )
    
    answer = ""
    for part in response.get('completion'):
        if 'chunk' in part:
            answer += part['chunk']['bytes'].decode('utf-8')
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer))

if __name__ == "__main__":
    app.run(port=10000)