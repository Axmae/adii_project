import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def _send_async(msg):
    try:
        msg.send()
    except Exception:
        pass


def _send_email(to_email, subject, template, context):
    html = render_to_string(template, context)
    msg = EmailMultiAlternatives(subject, "", settings.DEFAULT_FROM_EMAIL, [to_email])
    msg.attach_alternative(html, "text/html")
    threading.Thread(target=_send_async, args=(msg,), daemon=True).start()


def send_welcome_email(user):
    _send_email(
        user.email,
        "Bienvenue sur ADII — Gestion d'Habillement",
        "emails/welcome.html",
        {"user": user},
    )


def send_status_email(measurement):
    _send_email(
        measurement.user.email,
        f"Mise à jour — {measurement.get_status_display()}",
        "emails/status_update.html",
        {
            "m": measurement,
            "status": measurement.get_status_display(),
        },
    )
