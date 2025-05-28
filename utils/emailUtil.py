import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
def send_email(title, body):
    send_email(title, body, None)
def send_email(title, body, attachment_path=None):
    # 配置发件人和收件人
    sender_email = "1549598798@qq.com"
    receiver_email = "chenjiashudyx@163.com"
    password = "iizfrssliaunjebh"  # 替换为你的授权码

    # 创建邮件内容
    subject = title
    body = body

    # 创建 MIME 对象
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # 添加邮件正文
    message.attach(MIMEText(body, "plain"))
    # 添加附件
    if attachment_path:
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            message.attach(part)
    # 连接到 SMTP 服务器并发送邮件
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")
    finally:
        server.quit()