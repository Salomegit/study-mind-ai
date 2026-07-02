'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, Upload, MessageCircle, Brain } from 'lucide-react'
import { SignInButton, SignUpButton, UserButton } from '@clerk/nextjs'
import { useUser } from '@clerk/nextjs'

const navItems = [
  { href: '/', label: 'Home', icon: BookOpen },
  { href: '/upload', label: 'Upload', icon: Upload },
  { href: '/ask', label: 'Ask', icon: MessageCircle },
  { href: '/quiz', label: 'Quiz', icon: Brain },
]

export default function Navbar() {
  const pathname = usePathname()
  const { isSignedIn } = useUser()

  return (
    <nav className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2 text-xl font-bold">
            <span className="text-primary">Study</span>
            <span className="text-accent">Mind</span>
            <span className="text-secondary bg-secondary/20 px-2 py-0.5 rounded-md text-sm">AI</span>
          </Link>
          <div className="flex gap-6 items-center">
            {navItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2 transition-colors hover:text-primary ${
                  pathname === href ? 'text-primary border-b-2 border-primary pb-1' : 'text-text-muted'
                }`}
              >
                <Icon size={18} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            ))}
            {/* Auth Section */}
            <div className="flex items-center gap-2 ml-auto">
              {!isSignedIn ? (
                <>
                  <SignInButton mode="modal">
                    <button className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-md transition-colors">
                      Sign In
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="px-4 py-2 text-sm font-medium text-primary border border-primary hover:bg-primary/5 rounded-md transition-colors">
                      Sign Up
                    </button>
                  </SignUpButton>
                </>
              ) : (
                <UserButton />
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}