from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import boto3

app = Flask(__name__)

# ปรับชื่อตัวแปรให้ตรงกับ .env ของคุณ
line_bot_api = LineBotApi(os.getenv('LINE_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANEL_SECRET'))

# เชื่อมต่อ AWS Bedrock
client = boto3.client(
    'bedrock-agent-runtime', 
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # เรียกใช้ Bedrock Agent ตาม ID ใน .env
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
    
    if answer:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=answer))

if __name__ == "__main__":
    # Render มักจะใช้ Port 10000 เป็นค่าเริ่มต้น
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)