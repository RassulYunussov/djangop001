from django.conf import settings
from django.core.mail import send_mail
from django.template import loader


def send_emails(email, password, user):
    subject = 'Password'
    from_mail = settings.EMAIL_HOST_USER
    to_list = [email]
    email_tmp = loader.render_to_string(
        'web/email.html',
        {
            'user_data': '{} {}'.format(user.first_name, user.last_name),
            'password': password,
        }
    )
    send_mail(subject, password, from_mail, to_list, fail_silently=False, html_message=email_tmp)


def send_vilavi_id(email, password, user, vilavi_id):
    subject = 'Password'
    from_mail = settings.EMAIL_HOST_USER
    to_list = [email]
    email_tmp = loader.render_to_string(
        'web/email.html',
        {
            'user_data': '{} {}'.format(user.first_name, user.last_name),
            'vilavi_id': vilavi_id,
            'password': password,
        }
    )
    send_mail(subject, password, from_mail, to_list, fail_silently=False, html_message=email_tmp)
