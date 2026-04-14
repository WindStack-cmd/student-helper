import mysql.connector, os, requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'student_helper')
    )

def test_verification():
    print("--- Step 5: Email Verification ---")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT verification_token FROM users WHERE email = 'qa_test_unverified@example.com'")
    token = cursor.fetchone()['verification_token']
    
    verify_r = requests.get(f'http://127.0.0.1:5001/verify_email?token={token}')
    print(f'Verify Status: {verify_r.status_code}')
    print(f'Verify Body: {verify_r.json()}')
    
    cursor.execute("SELECT is_verified, verification_token FROM users WHERE email = 'qa_test_unverified@example.com'")
    res = cursor.fetchone()
    print(f'DB State: {res}')
    
    if res['is_verified'] == 1 and res['verification_token'] is None:
        print("Verification: PASS")
    else:
        print("Verification: FAIL")
        
    cursor.close()
    conn.close()

def test_post_verification():
    print("--- Step 6: Post-Verification Behavior ---")
    login_r = requests.post('http://127.0.0.1:5001/login', json={'email': 'qa_test_unverified@example.com', 'password': 'password123'})
    token = login_r.json().get('access_token')
    
    post_r = requests.post('http://127.0.0.1:5001/post_request', json={
        'title': 'QA Verified Request', 
        'description': 'This should go through now that I am verified and the system is working.', 
        'bounty': 0, 
        'email': 'qa_test_unverified@example.com'
    }, headers={'Authorization': f'Bearer {token}'})
    
    print(f'Post Status: {post_r.status_code}')
    print(f'Post Body: {post_r.json()}')
    
    if post_r.status_code == 201:
        print("Post-Verification: PASS")
    else:
        print("Post-Verification: FAIL")

def test_token_handling():
    print("--- Step 7: Token Handling ---")
    # Invalid
    inv_r = requests.get('http://127.0.0.1:5001/verify_email?token=invalid_token_here')
    print(f'Invalid Token Status: {inv_r.status_code} ({inv_r.json().get("error_code")})')
    
    # Expired
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET verification_token = 'expired_token', token_expires_at = %s WHERE email = 'qa_test_unverified@example.com'", 
                   (datetime.now() - timedelta(hours=1),))
    conn.commit()
    
    exp_r = requests.get('http://127.0.0.1:5001/verify_email?token=expired_token')
    print(f'Expired Token Status: {exp_r.status_code} ({exp_r.json().get("error_code")})')
    
    if inv_r.status_code == 404 and exp_r.status_code == 400:
        print("Token Handling: PASS")
    else:
        print("Token Handling: FAIL")
    cursor.close()
    conn.close()

def test_cleanup():
    print("--- Step 8: Auto Cleanup ---")
    conn = get_db()
    cursor = conn.cursor()
    # Create an old unverified user
    cursor.execute("INSERT INTO users (email, is_verified, created_unverified_at) VALUES ('old_user@example.com', 0, %s)", 
                   (datetime.now() - timedelta(days=8),))
    conn.commit()
    
    # Trigger cleanup (it runs on get_requests)
    requests.get('http://127.0.0.1:5001/get_requests')
    
    cursor.execute("SELECT * FROM users WHERE email = 'old_user@example.com'")
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if res is None:
        print("Cleanup: PASS")
    else:
        print("Cleanup: FAIL")

if __name__ == "__main__":
    test_verification()
    test_post_verification()
    test_token_handling()
    test_cleanup()
