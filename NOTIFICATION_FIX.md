# Notification Button CORS Error Fix

## Problem
The notification button was showing `ERROR_LOADING_NOTIFICATIONS` due to a CORS preflight request failure:
```
Access to fetch at 'http://127.0.0.1:5000/notifications' from origin 'http://127.0.0.1:5501' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
It does not have HTTP ok status.
```

## Root Cause
The `/notifications` endpoint was missing from the Flask backend (`app.py`), so when the browser sent a CORS preflight OPTIONS request, it received a 404 error instead of a valid response.

## Changes Made

### 1. Added Missing `/notifications` Endpoint (Backend)
**File:** `backend/app.py`

Added a new GET endpoint that:
- Extracts the user's email from the JWT token in the Authorization header
- Retrieves notifications from the database for that user
- Returns them as JSON with proper error handling
- Includes proper logging

```python
@app.route("/notifications", methods=["GET"])
def get_notifications():
    """FIX: Added notifications endpoint to fetch user notifications"""
    try:
        email = resolve_request_email()
        if not email:
            log_event("NOTIFICATIONS", "No email provided", "WARNING")
            return jsonify([]), 200

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, message, seen, created_at FROM notifications WHERE email = %s ORDER BY created_at DESC",
                (email,)
            )
            notifications = cursor.fetchall()
            
            # Convert datetime to string for JSON serialization
            for notif in notifications:
                if 'created_at' in notif and notif['created_at']:
                    notif['created_at'] = str(notif['created_at'])
            
            log_event("NOTIFICATIONS", f"Retrieved {len(notifications)} notifications for {email}", "INFO")
            return jsonify(notifications), 200
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        log_event("NOTIFICATIONS", f"Error retrieving notifications: {str(e)}", "ERROR")
        return jsonify([]), 500
```

### 2. Improved Error Handling in Frontend (Dashboard)
**File:** `webzip/js/dashboard.js`

- Added explicit `response.ok` check before parsing JSON
- Added better error logging to the console
- Added null/undefined check for the response array

### 3. Fixed Pre-existing Route Duplicates
**File:** `backend/app.py`

Removed duplicate route definitions that were causing Flask to raise AssertionError:
- Removed duplicate `/get_answers/<int:request_id>` route (line 770)
- Removed duplicate `/accept_answer` route (line 602)

## How It Works

1. **CORS Configuration** - Already properly configured in `app.py`:
   ```python
   ALLOWED_ORIGINS = "http://localhost:8000,http://localhost:3000,http://127.0.0.1:5501"
   CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)
   ```

2. **Frontend Request** - Dashboard sends request with JWT token:
   ```javascript
   const headers = getAuthHeaders(); // Includes "Authorization": "Bearer <token>"
   const response = await fetch("http://127.0.0.1:5000/notifications", { headers });
   ```

3. **Backend Processing** - Endpoint extracts email and returns notifications:
   - JWT token is verified using `resolve_request_email()`
   - Notifications are fetched from the database
   - Results are returned as JSON

## Testing

To verify the fix works:
1. Open the dashboard in your browser (http://127.0.0.1:5501)
2. Click the notification button
3. Notifications should now load without errors
4. Any existing notifications will be displayed
5. If no notifications exist, you'll see "NO_NEW_NOTIFICATIONS"

## Notes

- The CORS preflight issue is resolved because the endpoint now exists and properly responds to OPTIONS requests
- flask-cors automatically handles CORS headers and preflight requests
- The endpoint uses proper JWT authentication via the Authorization header
- All notifications are user-specific, fetched based on their authenticated email
