"""
Get admin user info and try to login
"""
import sys
sys.path.insert(0, "PramaIAServer")

from backend.db.database import SessionLocal
from backend.db.models import User

db = SessionLocal()

try:
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        print("Admin user found:")
        print(f"  ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  Is Active: {admin.is_active}")
        print(f"  User ID (UUID): {admin.user_id}")
        print("\nTo test login, use:")
        print("  - Username: admin")
        print("  - Password: (try common defaults or check .env)")
        print("\nCommon passwords to try:")
        print("  - admin")
        print("  - admin123")
        print("  - password")
        print("  - test123")
    else:
        print("✗ Admin user not found")
        
        # List all users
        users = db.query(User).all()
        print(f"\nAvailable users ({len(users)}):")
        for u in users:
            print(f"  - {u.username} (role: {u.role})")
            
finally:
    db.close()
