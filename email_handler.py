import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import url_for

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = 'noreply@chatapp.com'

def send_registration_email(user_email, username):
    """Send a registration confirmation email to the user."""
    message = Mail(
        from_email=Email(FROM_EMAIL),
        to_emails=To(user_email),
        subject='Registration Confirmation - AI Chat Assistant',
        content=Content('text/html', f'''
            <h2>Thank you for registering, {username}!</h2>
            <p>Your registration is pending administrator approval. You will receive another email once your account has been approved.</p>
            <p>Thank you for your patience!</p>
        ''')
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Error sending registration email: {str(e)}")
        return False

def send_approval_email(user_email, username, approved=True):
    """Send an email notifying the user about their approval status."""
    if approved:
        subject = 'Account Approved - AI Chat Assistant'
        content = f'''
            <h2>Welcome aboard, {username}!</h2>
            <p>Your account has been approved. You can now log in and start using the AI Chat Assistant.</p>
            <p>Click <a href="{{{{ login_url }}}}">here</a> to login.</p>
        '''
    else:
        subject = 'Account Registration Update - AI Chat Assistant'
        content = f'''
            <h2>Registration Update</h2>
            <p>We regret to inform you that your registration request has not been approved at this time.</p>
            <p>If you believe this is an error, please contact the administrator.</p>
        '''
    
    message = Mail(
        from_email=Email(FROM_EMAIL),
        to_emails=To(user_email),
        subject=subject,
        content=Content('text/html', content)
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print(f"Error sending approval email: {str(e)}")
        return False
