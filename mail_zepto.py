import os
import base64
import smtplib, ssl
import json

#needed for attachment
import smtplib  
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
#List of all mimetype per extension: http://help.dottoro.com/lapuadlp.php  or http://mime.ritey.com/



CRED = "srmc_mathiitm.json"

SMTP_SERVER = "smtp.zeptomail.in"

## Get creds, prepare message and send it
def create_message_and_send(sender, to, subject,  message_text_plain="", message_text_html="", attached_file="", cc="", replyto=""):
    ## without attachment

    
    creds = json.load(open(CRED, "r"))
    
    if replyto=="":
        replyto=creds["replyemail"]

    context = ssl.create_default_context()
    server = smtplib.SMTP(SMTP_SERVER, 587)
    server.starttls(context=context)
    server.login(creds["username"], creds["password"])

    print ("successfully sent")

    if attached_file=="":
        message_without_attachment = create_message_without_attachment(sender, to, cc, subject, message_text_html, message_text_plain, replyto)
        send_Message_without_attachment(server, message_without_attachment)
    else:
        message_with_attachment = create_Message_with_attachment(sender, to, cc, subject, message_text_plain, message_text_html, replyto, attached_file)
        send_Message_with_attachment(server, message_with_attachment, attached_file)

def create_message_without_attachment (sender, to, cc="", subject="", message_text_html="", message_text_plain="", replyto=""):
    
    if replyto=="":
        replyto=sender

    #Create message container
    message = MIMEMultipart('alternative') # needed for both plain & HTML (the MIME type is multipart/alternative)
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to
    message['CC'] = cc
    message['Reply-To'] = replyto

    #Create the body of the message (a plain-text and an HTML version)
    message.attach(MIMEText(message_text_plain, 'plain'))
    message.attach(MIMEText(message_text_html, 'html'))

    return message



def create_Message_with_attachment(sender, to, cc="", subject="", message_text_plain="", message_text_html="", replyto="", attached_file=""):
    """Create a message for an email.

    message_text: The text of the email message.
    attached_file: The path to the file to be attached.

    Returns:
    An object containing a base64url encoded email object.
    """

    ##An email is composed of 3 part :
        #part 1: create the message container using a dictionary { to, from, subject }
        #part 2: attach the message_text with .attach() (could be plain and/or html)
        #part 3(optional): an attachment added with .attach() 

    if replyto=="":
        replyto=sender

    ## Part 1
    message = MIMEMultipart() #when alternative: no attach, but only plain_text
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to
    message['CC'] = cc
    message['Reply-To'] = replyto


    ## Part 2   (the message_text)
    # The order count: the first (html) will be use for email, the second will be attached (unless you comment it)
    message.attach(MIMEText(message_text_html, 'html'))
    message.attach(MIMEText(message_text_plain, 'plain'))

    my_mimetype, encoding = mimetypes.guess_type(attached_file)

    # If the extension is not recognized it will return: (None, None)
    # If it's an .mp3, it will return: (audio/mp3, None) (None is for the encoding)
    #for unrecognized extension it set my_mimetypes to  'application/octet-stream' (so it won't return None again). 
    if my_mimetype is None or encoding is not None:
        my_mimetype = 'application/octet-stream' 


    main_type, sub_type = my_mimetype.split('/', 1)# split only at the first '/'
    # if my_mimetype is audio/mp3: main_type=audio sub_type=mp3

    #-----3.2  creating the attachment
        #you don't really "attach" the file but you attach a variable that contains the "binary content" of the file you want to attach

        #option 1: use MIMEBase for all my_mimetype (cf below)  - this is the easiest one to understand
        #option 2: use the specific MIME (ex for .mp3 = MIMEAudio)   - it's a shorcut version of MIMEBase

    #this part is used to tell how the file should be read and stored (r, or rb, etc.)
    if main_type == 'text':
        print("\nAttachment type: text\n")
        temp = open(attached_file, 'r')  # 'rb' will send this error: 'bytes' object has no attribute 'encode'
        attachment = MIMEText(temp.read(), _subtype=sub_type)
        temp.close()

    elif main_type == 'image':
        print("\nAttachment type: image\n")
        temp = open(attached_file, 'rb')
        attachment = MIMEImage(temp.read(), _subtype=sub_type)
        temp.close()

    elif main_type == 'audio':
        print("\nAttachment type: audio\n")
        temp = open(attached_file, 'rb')
        attachment = MIMEAudio(temp.read(), _subtype=sub_type)
        temp.close()            

    elif main_type == 'application' and sub_type == 'pdf':   
        temp = open(attached_file, 'rb')
        attachment = MIMEApplication(temp.read(), _subtype=sub_type)
        temp.close()

    else:                              
        attachment = MIMEBase(main_type, sub_type)
        temp = open(attached_file, 'rb')
        attachment.set_payload(temp.read())
        temp.close()

    #-----3.3 encode the attachment, add a header and attach it to the message
    # encoders.encode_base64(attachment)  #not needed (cf. randomfigure comment)
    #https://docs.python.org/3/library/email-examples.html

    filename = os.path.basename(attached_file)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename) # name preview in email
    message.attach(attachment) 


    return message



def send_Message_without_attachment(server, message):
    try:
        server.send_message(message)
        # print(attached_file)
        print (f'Message sent (without attachment)\n\n')
        # return body
    except Exception as error:
        print (f'An error occurred: {error}')




def send_Message_with_attachment(server, message_with_attachment, attached_file):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me" can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    try:
        server.send_message(message_with_attachment)
        # print(attached_file)
        print (f'Message sent (with attachment) File: {attached_file}\n\n')
        # return message_sent
    except Exception as error:
        print (f'An error occurred: {error}')


def main():
    to = "ee23b189@smail.iitm.ac.in"
    sender = "ee23b189@smail.iitm.ac.in"
    subject = "DC results"
    message_text_html  = r'<br> Hello KK. You have been selected as a DC. <br> <hr>'
    message_text_plain = ""
    attached_file = ""
    create_message_and_send(sender, to, subject, message_text_plain, message_text_html, attached_file)


if __name__ == '__main__':
        main()