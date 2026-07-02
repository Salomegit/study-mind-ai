/**
 * Client-side auth utilities for protected routes
 * These components should wrap pages that require authentication
 */

'use client'

import { useUser } from '@clerk/nextjs'
import { ReactNode } from 'react'
import Link from 'next/link'

export type UserRole = 'admin' | 'user'

/**
 * Component to check if user is signed in
 * Shows children if signed in, otherwise shows sign-in prompt
 */
export function ProtectedPage({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useUser()

  if (!isLoaded) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  if (!isSignedIn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <h1 className="text-3xl font-bold text-text">Please sign in to continue</h1>
        <p className="text-text-muted">You need to be authenticated to access this page.</p>
        <Link href="/" className="mt-4 px-6 py-2 bg-primary text-white rounded-md hover:bg-primary/90">
          Go Home
        </Link>
      </div>
    )
  }

  return <>{children}</>
}

/**
 * Component to check user role
 * Shows children if user has the required role
 */
export function AdminOnly({ children }: { children: ReactNode }) {
  const { user, isLoaded } = useUser()

  if (!isLoaded) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  const role = user?.publicMetadata?.role as UserRole | undefined

  if (role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <h1 className="text-3xl font-bold text-text">Access Denied</h1>
        <p className="text-text-muted">You do not have admin permissions to access this page.</p>
        <Link href="/" className="mt-4 px-6 py-2 bg-primary text-white rounded-md hover:bg-primary/90">
          Go Home
        </Link>
      </div>
    )
  }

  return <>{children}</>
}

/**
 * Hook to check if current user is admin
 */
export function useIsAdmin(): boolean {
  const { user } = useUser()
  return (user?.publicMetadata?.role as UserRole | undefined) === 'admin'
}

/**
 * Hook to get current user's role
 */
export function useUserRole(): UserRole {
  const { user } = useUser()
  return (user?.publicMetadata?.role as UserRole | undefined) || 'user'
}
