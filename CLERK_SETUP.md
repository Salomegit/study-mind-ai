# Clerk Authentication Setup Guide

This project uses **Clerk** for authentication with role-based access control.

## Quick Start

### 1. Get Your Clerk API Keys

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Create a new application (or use existing)
3. Navigate to **API Keys** section
4. Copy your keys:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (public key)
   - `CLERK_SECRET_KEY` (secret key)

### 2. Configure Environment Variables

Create or update `.env.local` in the `frontend/` directory:

```env
# Clerk Authentication Keys
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_publishable_key_here
CLERK_SECRET_KEY=your_secret_key_here

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Your App

```bash
npm run dev
```

Visit `http://localhost:3000` and you'll see:
- **Sign In** / **Sign Up** buttons in the navbar (when not authenticated)
- **User Button** with profile menu (when authenticated)

## Authentication Flow

### Protected Routes

The following routes require authentication:
- `/upload` - Upload study materials
- `/ask` - Ask questions
- `/quiz` - Take quizzes

Unauthenticated users are redirected to sign in.

### Session Memory

When a user signs in:
- Their `userId` from Clerk is captured
- Session history is stored server-side in SQLite by `session_id`
- Auth tokens are automatically included in API requests

## Role-Based Access Control (RBAC)

### Admin vs User Roles

Users can have two roles:
- **`admin`** - Can manage all content (future: delete/edit collections)
- **`user`** - Regular user (default)

### Setting User Roles

#### Option 1: Via Clerk Dashboard (Recommended for Now)

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Navigate to **Users**
3. Select a user
4. Scroll to **Public Metadata**
5. Add or update:
   ```json
   {
     "role": "admin"
   }
   ```
6. Save

#### Option 2: Programmatically (Backend API)

You can set roles via the Clerk API in your backend. Add this to `backend/main.py`:

```python
from clerk_backend_api import Clerk

clerk_client = Clerk(api_key=os.getenv("CLERK_SECRET_KEY"))

@app.post("/admin/set-role")
async def set_user_role(user_id: str, role: str):
    """Set a user's role (admin only)"""
    await auth.protect()  # Only authenticated users
    
    # In production, verify the requester is admin
    updated_user = clerk_client.users.update(
        user_id=user_id,
        public_metadata={"role": role}
    )
    return {"user_id": user_id, "role": role}
```

### Frontend: Checking Roles

#### In Client Components

```tsx
import { useUser } from '@clerk/nextjs'
import { AdminOnly, ProtectedPage } from '@/components/ProtectedRoute'

// Protect route - auth required
export default function Page() {
  return (
    <ProtectedPage>
      <YourContent />
    </ProtectedPage>
  )
}

// Admin-only route
export default function AdminPage() {
  return (
    <ProtectedPage requiredRole="admin">
      <AdminPanel />
    </ProtectedPage>
  )
}

// Manual role checking
export function MyComponent() {
  const { user } = useUser()
  const isAdmin = user?.publicMetadata?.role === 'admin'
  
  return isAdmin ? <AdminView /> : <UserView />
}
```

### Backend: Checking Roles

```python
from lib.auth import getUserRole, isAdmin

@app.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str):
    """Only admins can delete collections"""
    if not await isAdmin():
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Delete collection logic
    return {"deleted": collection_id}
```

## Frontend Components

### ProtectedRoute Component

Wraps pages to require authentication:

```tsx
<ProtectedPage>
  <YourPageContent />
</ProtectedPage>
```

### Protected by Role

```tsx
<ProtectedPage requiredRole="admin">
  <AdminContent />
</ProtectedPage>
```

### Current Status

✅ **Implemented:**
- Clerk sign-in/sign-up UI in navbar
- Route protection middleware (`/upload`, `/ask`, `/quiz`)
- Client-side auth on protected pages
- Role metadata support

⏳ **Ready for Implementation:**
- Backend role checks for sensitive operations
- Admin dashboard for role management
- Admin-only collection deletion/editing

## Backend Integration

To integrate with your FastAPI backend, add Clerk validation:

```python
# backend/services/auth.py
from jose import JWTError
import requests

async def verify_clerk_token(token: str) -> str:
    """Verify Clerk JWT and return user_id"""
    # Token validation happens via Clerk's JWKS
    # This is typically handled by middleware
    pass

@app.get("/protected-endpoint")
async def protected(request: Request):
    """Example protected endpoint"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing auth")
    
    # Verify token with Clerk
    # Extract user_id from token
    # Proceed with user-specific logic
    return {"message": "Authorized!"}
```

## Troubleshooting

### 1. "Missing env variables"

Ensure both keys are in `.env.local`:
```bash
echo $NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY  # Should print your key
echo $CLERK_SECRET_KEY  # Should print your secret
```

### 2. "Sign in button doesn't work"

- Check that `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is correct
- Verify your Clerk app is active in dashboard
- Clear browser cache and restart dev server

### 3. "User data not persisting"

- Ensure middleware.ts is in `frontend/` (not in `app/`)
- Verify matcher includes your protected routes
- Check that `ClerkProvider` wraps entire app in layout.tsx

### 4. "Roles not showing up"

- Go to Clerk dashboard
- Edit user → Public Metadata
- Add `{"role": "admin"}` manually
- Refresh page (roles cache for 5 minutes)

## Next Steps

1. ✅ Get Clerk API keys from dashboard
2. ✅ Add to `.env.local`
3. ✅ Test sign-in/sign-up
4. ⏳ Set admin roles for test users
5. ⏳ Add backend Clerk validation
6. ⏳ Implement admin dashboard
7. ⏳ Add role-based API endpoints

## Resources

- [Clerk Docs](https://clerk.com/docs)
- [Clerk Next.js Guide](https://clerk.com/docs/nextjs/get-started)
- [Clerk Metadata](https://clerk.com/docs/users/metadata)
- [Clerk Organizations](https://clerk.com/docs/guides/organizations/overview)
