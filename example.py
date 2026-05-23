import mail_zepto as mail

# File to store credentials in
# mail.CRED = "meth.json"

# Subject of mail
SUBJECT = "Some Subject"

# The HTML file to be embedded
HTML_FILE = "example.html"

# The file to be attached
ATTACH = "attachment.txt"

# Dict of email prefixes and Name
REC = {"achintyar":"Achintya"}


# Read the HTML file
def getmesg(file):
    with open(file, "r") as f:
        return f.read()


# Send mails to all members in rec
def send_mails(records, subject, message, attachment):
    itr=0
    for entry in records:
        itr+=1
        
        # Replace placeholder text with entry
        unique_message=message.replace("random_placeholder_text", records[entry]) 

        email=entry.lower()+"@smail.iitm.ac.in"
        
        # Print info
        print(f"{itr}  {email}, {records[entry]}")
        
        mail.create_message_and_send(
             sender="SRMC <noreply@srmc.mathiitm.com>", 
             to=email, 
             subject=subject, 
             message_text_html=unique_message, 
        #      attached_file=attachment
        )

def main():
        
        # Read into MESSAGE
        message = getmesg(HTML_FILE)
        
        # Send mail
        send_mails(REC, SUBJECT, message, ATTACH)


if __name__ == '__main__':
        main()