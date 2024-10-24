import os
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.urls import reverse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import UserCredentials


# Constants
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only (HTTP)

### Note: For production, ensure you use HTTPS and remove OAUTHLIB_INSECURE_TRANSPORT.

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'profile', 'email']
REDIRECT_URI = 'http://localhost:8000/auth/callback/'  # Adjust as needed

# Create your views here.

def google_login(request):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    request.session['state'] = state
    return redirect(authorization_url)

def google_callback(request):
    state = request.session.get('state')
    if not state:
        messages.error(request, "State parameter missing in session.")
        return redirect('login')

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )

    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials

    # Get user info
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()

    email = user_info.get('email')
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')

    # Authenticate user
    user, created = User.objects.get_or_create(username=email, defaults={
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
    })

    # Save credentials in the database
    creds, created = UserCredentials.objects.get_or_create(user=user)
    creds.token = credentials.token
    creds.refresh_token = credentials.refresh_token
    creds.token_uri = credentials.token_uri
    creds.client_id = credentials.client_id
    creds.client_secret = credentials.client_secret
    creds.scopes = ','.join(credentials.scopes)
    creds.save()

    login(request, user)
    messages.success(request, f"Welcome, {first_name}!")

    return redirect('home')  # Redirect to your application's home page

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')
