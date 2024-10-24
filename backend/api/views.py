from django.shortcuts import render
import os
from django.http import JsonResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Create your views here.
def test_google_api(request):
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )

    service = build('drive', 'v3', credentials=credentials)
    # List the first 10 files the service account has access to
    results = service.files().list(pageSize=10).execute()
    items = results.get('files', [])

    return JsonResponse({'files': items})