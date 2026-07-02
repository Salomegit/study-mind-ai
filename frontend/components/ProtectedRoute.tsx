/**
 * Protected route components for authenticated pages
 * Wrap pages that require authentication/authorization
 */

'use client'

import { useUser } from '@clerk/nextjs'
import { ReactNode } from 'react'
import Link from 'next/link'

export type UserRole = 'admin' | 'user'

interface ProtectedPageProps {
  children: ReactNode
  requiredRole?: UserRole
  fallbackMessage?: string
}

/**
 * Component to protect routes - requires authentication
 * Shows children if signed in, otherwise shows sign-in prompt
 */
export function ProtectedPage({
  children,
  requiredRole,
  fallbackMessage,
}: ProtectedPageProps) {
  const { isLoaded, isSignedIn, user } = useUser()

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-text mb-2">Loading...</h1>
          <p className="text-text-muted">Please wait</p>
        </div>
      </div>
    )
  }

  if (!isSignedIn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 px-4">
        <h1 className="text-3xl font-bold text-text">Authentication Required</h1>
        <p className="text-text-muted max-w-md text-center">
          You need to sign in to access this page. Create an account if you don't have one yet.
        </p>
        <div className="flex gap-2 mt-4">
          <Link href="/" className="px-6 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors">
            Go Home
          </Link>
        </div>
      </div>
    )
  }

  // Check role if specified
  if (requiredRole) {
    const userRole = (user?.publicMetadata?.role as UserRole | undefined) || 'user'
    if (userRole !== requiredRole) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 px-4">
          <h1 className="text-3xl font-bold text-text">Access Denied</h1>
          <p className="text-text-muted max-w-md text-center">
            {fallbackMessage ||
              `You do not have permission to access this page. Required role: ${requiredRole}`}
          </p>
          <Link href="/" className="mt-4 px-6 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors">
            Go Home
          </Link>
        </div>
      )
    }
  }

  return <>{children}</>
}
