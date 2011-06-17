import os
import smtplib
import mimetypes
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase      import MIMEBase
from email.MIMEText      import MIMEText
from email.MIMEAudio     import MIMEAudio
from email.MIMEImage     import MIMEImage
from email.Encoders      import encode_base64

def send_mail(subject,text,attachment_file_paths,user,password,recipient):

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for attachment_file_path in attachment_file_paths:
        msg.attach(get_attachment(attachment_file_path))
    
    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(user, password)
    mailServer.sendmail(user, recipient, msg.as_string())
    mailServer.close()
    
    print('Sent email to %s.' % recipient)

def get_attachment(attachment_file_path):

    content_type, encoding = mimetypes.guess_type(attachment_file_path)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    
    main_type, sub_type = content_type.split('/', 1)
    file = open(attachment_file_path, 'rb')
    
    attachment = MIMEBase(main_type, sub_type)    
    attachment.set_payload(file.read())
    encode_base64(attachment)

    file.close()

    attachment.add_header('Content-Disposition', 'attachment',filename=os.path.basename(attachment_file_path))
    return attachment
