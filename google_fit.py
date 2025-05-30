import os
import json
import flask
import requests
import logging
from flask import redirect, request, url_for, session
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import datetime

# This file handles Google Fit API integration

# OAuth 2.0 scopes for Google Fit API
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Path to client configuration file
CLIENT_SECRET_FILE = 'client_secret.json'

def get_client_config():
    """Load client configuration from the client_secret.json file"""
    try:
        with open(CLIENT_SECRET_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading client secret file: {e}")
        return None

def create_oauth_flow(redirect_uri):
    """Create OAuth flow for Google Fit API authentication."""
    client_config = get_client_config()
    if not client_config:
        return None

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )

    # Dynamically set the redirect URI based on the request's host
    flow.redirect_uri = redirect_uri
    return flow

def get_fitness_service(credentials):
    """Build and return the Google Fitness service"""
    return build('fitness', 'v1', credentials=credentials)

def get_steps_data(service, start_time, end_time):
    """Get daily step count data from Google Fit"""
    try:
        datasource = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": datasource
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        daily_steps = []
        for bucket in response.get('bucket', []):
            day = datetime.datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000).strftime('%Y-%m-%d')
            steps = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        steps += value.get('intVal', 0)
            daily_steps.append({'date': day, 'steps': steps})
        return daily_steps
    except Exception as e:
        print(f"Error fetching step data: {e}")
        return []


def get_calories_data(service, start_time, end_time):
    """Get daily calories data from Google Fit"""
    try:
        datasource = "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended"
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.calories.expended",
                "dataSourceId": datasource
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        daily_calories = []
        for bucket in response.get('bucket', []):
            day = datetime.datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000).strftime('%Y-%m-%d')
            calories = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        calories += value.get('fpVal', 0)
            daily_calories.append({'date': day, 'calories': int(calories)})
        return daily_calories
    except Exception as e:
        print(f"Error fetching calories data: {e}")
        return []


def get_activity_data(service, start_time, end_time):
    """Get daily activity minutes data from Google Fit"""
    try:
        datasource = "derived:com.google.active_minutes:com.google.android.gms:merge_active_minutes"
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.active_minutes",
                "dataSourceId": datasource
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        response = service.users().dataset().aggregate(userId="me", body=body).execute()
        daily_minutes = []
        for bucket in response.get('bucket', []):
            day = datetime.datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000).strftime('%Y-%m-%d')
            minutes = 0
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    for value in point.get('value', []):
                        minutes += value.get('intVal', 0)
            daily_minutes.append({'date': day, 'activity_minutes': minutes})
        return daily_minutes
    except Exception as e:
        print(f"Error fetching activity data: {e}")
        return []


def get_user_email(credentials):
    """Get user email from Google API"""
    try:
        # Build the People API service
        people_service = build('people', 'v1', credentials=credentials)
        
        # Get the user's profile information
        profile = people_service.people().get(
            resourceName='people/me',
            personFields='emailAddresses,names'
        ).execute()
        
        # Extract primary email
        email_addresses = profile.get('emailAddresses', [])
        if email_addresses:
            for email in email_addresses:
                if email.get('metadata', {}).get('primary', False):
                    return email.get('value')
            
            # If no primary email is found, return the first one
            return email_addresses[0].get('value')
        
        return "Unknown"
    except Exception as e:
        print(f"Error getting user email: {e}")
        return "Unknown"

def get_fit_data():
    """Gather all fitness data and return as a dictionary with daily values"""
    # Check if user is authenticated
    if 'credentials' not in session:
        logging.error("No credentials found in session.")
        return None

    # Load credentials from the session
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])

    # Get user email
    email = get_user_email(credentials)
    logging.debug(f"User email: {email}")

    # Build the fitness service
    fitness_service = get_fitness_service(credentials)

    # Calculate time range (last 7 days)
    end_time = int(datetime.datetime.now().timestamp() * 1000)
    start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days in milliseconds

    logging.debug(f"Time range: Start - {start_time}, End - {end_time}")

    # Get fitness data
    steps = get_steps_data(fitness_service, start_time, end_time)
    logging.debug(f"Steps data: {steps}")

    calories = get_calories_data(fitness_service, start_time, end_time)
    logging.debug(f"Calories data: {calories}")

    activity = get_activity_data(fitness_service, start_time, end_time)
    logging.debug(f"Activity minutes data: {activity}")

    # Save the updated credentials back to the session
    session['credentials'] = credentials_to_dict(credentials)

    return {
        'email': email,
        'steps': steps,
        'calories': calories,
        'activity_minutes': activity,
        'period': '7 days',
        'daily': True
    }

def credentials_to_dict(credentials):
    """Convert credentials to a dictionary for session storage"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def init_google_fit_routes(app):
    """Initialize Google Fit API routes for the Flask application"""
    
    # Enable HTTPS locally for OAuth (only for development)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Add logging to debug the redirect_uri
    logging.basicConfig(level=logging.DEBUG)
    
    # Add route to initiate OAuth flow
    @app.route('/google_fit_auth')
    def google_fit_auth():
        """Initiate OAuth flow and dynamically set redirect_uri."""
        # Dynamically determine the redirect URI based on the request's host
        redirect_uri = url_for('google_fit_callback', _external=True)
        logging.debug(f"Redirect URI being used: {redirect_uri}")

        flow = create_oauth_flow(redirect_uri)

        if not flow:
            return "Error: Could not load client configuration", 500

        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )

        # Store the state in the session
        session['state'] = state

        return redirect(authorization_url)
    
    # Add route for OAuth callback
    @app.route('/google_fit_callback')
    def google_fit_callback():
        """Handle the OAuth callback and log state for debugging."""
        # Log the state parameter received
        logging.debug(f"State received: {request.args.get('state')}")
        logging.debug(f"State stored in session: {session.get('state')}")

        # Check for state mismatch
        state = session.get('state')
        if not state or state != request.args.get('state'):
            return "Error: State mismatch. Possible CSRF attack", 403
        
        # Create flow instance
        flow = create_oauth_flow(url_for('google_fit_callback', _external=True))
        
        if not flow:
            return "Error: Could not load client configuration", 500
        
        # Exchange authorization code for access token
        flow.fetch_token(authorization_response=request.url)
        
        # Get credentials and store in session
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        
        # Redirect to analytics page
        return redirect(url_for('analytics_page'))
    
    # API endpoint to get fitness data
    @app.route('/api/fitness_data')
    def fitness_data():
        if 'credentials' not in session:
            return flask.jsonify({'error': 'Not authenticated with Google Fit'})
        
        fit_data = get_fit_data()
        if fit_data:
            return flask.jsonify(fit_data)
        else:
            return flask.jsonify({'error': 'Failed to fetch fitness data'})
    
    # Add route to disconnect from Google Fit
    @app.route('/google_fit_disconnect')
    def google_fit_disconnect():
        # Clear the credentials from the session
        if 'credentials' in session:
            del session['credentials']
        
        # Redirect back to analytics page
        return redirect(url_for('analytics_page'))

    # Add route to redirect /fitness_data to /api/fitness_data
    @app.route('/fitness_data')
    def redirect_fitness_data():
        """Redirect /fitness_data to /api/fitness_data."""
        return redirect(url_for('fitness_data'))

    @app.route('/api/auth/google/callback')
    def api_auth_google_callback():
        """Redirect /api/auth/google/callback to /google_fit_callback."""
        return redirect(url_for('google_fit_callback'))