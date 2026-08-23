import os
from firebase_admin import initialize_app
from firebase_functions import https_fn
from django.core.wsgi import get_wsgi_application
from werkzeug.wrappers import Response

# Initialize Firebase Admin SDK
initialize_app()

# Initialize Django WSGI application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainproj.settings')
django_application = get_wsgi_application()

@https_fn.on_request(memory=512, timeout_sec=60)
def api(req: https_fn.Request) -> https_fn.Response:
    """Entrypoint for Firebase Cloud Functions (Python) to serve Django."""
    return Response.from_app(django_application, req.environ)
