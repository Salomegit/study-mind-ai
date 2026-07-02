import { auth } from '@clerk/nextjs/server'

/**
 * Clerk Role-Based Access Control
 * 
 * Roles are stored in user metadata under publicMetadata.role
 * You can set this manually in the Clerk dashboard or via the API
 */

export type UserRole = 'admin' | 'user'

/**
 * Get the current user's role from Clerk metadata
 */
export async function getUserRole(): Promise<UserRole | null> {
  const { userId, sessionClaims } = await auth()
  
  if (!userId) return null
  
  // Access role from public metadata
  const role = sessionClaims?.metadata?.role as UserRole | undefined
  return role || 'user' // Default to 'user' if not set
}

/**
 * Check if current user has a specific role
 */
export async function hasRole(requiredRole: UserRole): Promise<boolean> {
  const role = await getUserRole()
  return role === requiredRole
}

/**
 * Check if current user is admin
 */
export async function isAdmin(): Promise<boolean> {
  return hasRole('admin')
}

/**
 * Protect a route - redirects to sign-in if not authenticated
 */
export async function protectRoute() {
  const { userId } = await auth()
  if (!userId) {
    throw new Error('Unauthorized: Please sign in')
  }
  return userId
}

/**
 * Protect a route with role requirement
 */
export async function protectRouteWithRole(requiredRole: UserRole) {
  const userId = await protectRoute()
  const role = await getUserRole()
  
  if (role !== requiredRole) {
    throw new Error(`Unauthorized: Required role is ${requiredRole}`)
  }
  
  return userId
}
