import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import url_for

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM_EMAIL = os.environ.get('VERIFIED_SENDER_EMAIL')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')

def send_registration_email(user_email, username):
    """Send a registration confirmation email to the user."""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        print("SendGrid configuration missing")
        return False
        
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=user_email,
            subject='Registration Confirmation - AI Chat Assistant',
            html_content=f'''
                <h2>Thank you for registering, {username}!</h2>
                <p>Your registration is pending administrator approval. You will receive another email once your account has been approved.</p>
                <p>Thank you for your patience!</p>
            '''
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code >= 400:
            print(f"SendGrid API error: {response.status_code} - {response.body}")
            return False
            
        print(f"Registration email sent successfully. Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending registration email: {str(e)}")
        return False

def send_admin_notification_email(new_user_email, new_username):
    """Send a notification email to admin about new user registration."""
    if not SENDGRID_API_KEY or not FROM_EMAIL or not ADMIN_EMAIL:
        print("SendGrid configuration or admin email missing")
        return False
        
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=ADMIN_EMAIL,
            subject='New User Registration - AI Chat Assistant',
            html_content=f'''
                <h2>New User Registration</h2>
                <p>A new user has registered and is awaiting approval:</p>
                <ul>
                    <li><strong>Username:</strong> {new_username}</li>
                    <li><strong>Email:</strong> {new_user_email}</li>
                </ul>
                <p>Please log in to the admin panel to approve or reject this registration.</p>
            '''
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code >= 400:
            print(f"SendGrid API error: {response.status_code} - {response.body}")
            return False
            
        print(f"Admin notification email sent successfully. Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending admin notification email: {str(e)}")
        return False

def send_approval_email(user_email, username, approved=True):
    """Send an email notifying the user about their approval status."""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        print("SendGrid configuration missing")
        return False
        
    try:
        if approved:
            subject = 'Account Approved - AI Chat Assistant'
            content = f'''
                <h2>Welcome aboard, {username}!</h2>
                <p>Your account has been approved. You can now log in and start using the AI Chat Assistant.</p>
                <p>Click <a href="https://{os.environ.get('REPL_SLUG', '')}.{os.environ.get('REPL_OWNER', '')}.repl.co/login">here</a> to login.</p>
            '''
        else:
            subject = 'Account Registration Update - AI Chat Assistant'
            content = f'''
                <h2>Registration Update</h2>
                <p>We regret to inform you that your registration request has not been approved at this time.</p>
                <p>If you believe this is an error, please contact the administrator.</p>
            '''
        
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=user_email,
            subject=subject,
            html_content=content
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code >= 400:
            print(f"SendGrid API error: {response.status_code} - {response.body}")
            return False
            
        print(f"Approval email sent successfully. Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending approval email: {str(e)}")
        return False
