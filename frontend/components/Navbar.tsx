'use client'
import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, Upload, MessageCircle, Brain, Menu, X } from 'lucide-react'
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
  const { isSignedIn, isLoaded } = useUser()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const toggleMenu = () => setIsMenuOpen((open) => !open)
  const closeMenu = () => setIsMenuOpen(false)

  // Close the mobile menu whenever the route changes.
  useEffect(() => {
    closeMenu()
  }, [pathname])

  // Close on outside click / Escape, and lock body scroll while open.
  useEffect(() => {
    if (!isMenuOpen) return

    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        closeMenu()
      }
    }
    const handleEscape = (e) => {
      if (e.key === 'Escape') closeMenu()
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isMenuOpen])

  return (
    <nav
      ref={menuRef}
      className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link
            href="/"
            onClick={closeMenu}
            className="flex items-center gap-2 text-xl font-bold flex-shrink-0 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            <span className="text-primary">Study</span>
            <span className="text-accent">Mind</span>
            <span className="text-secondary bg-secondary/20 px-2 py-0.5 rounded-md text-sm">AI</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex gap-6 items-center flex-1 ml-8">
            {navItems.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`relative flex items-center gap-2 py-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-md ${
                    isActive ? 'text-primary' : 'text-text-muted hover:text-primary'
                  }`}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                  <span
                    className={`absolute -bottom-[1px] left-0 right-0 h-0.5 bg-primary rounded-full transition-transform origin-left duration-200 ${
                      isActive ? 'scale-x-100' : 'scale-x-0'
                    }`}
                  />
                </Link>
              )
            })}
          </div>

          {/* Desktop Auth Section */}
          <div className="hidden md:flex items-center gap-4">
            {isLoaded && !isSignedIn ? (
              <>
                <SignInButton mode="modal">
                  <button className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 active:scale-[0.97] rounded-md transition-all">
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="px-4 py-2 text-sm font-medium text-primary border border-primary hover:bg-primary/5 active:scale-[0.97] rounded-md transition-all">
                    Sign Up
                  </button>
                </SignUpButton>
              </>
            ) : isLoaded && isSignedIn ? (
              <UserButton />
            ) : (
              <div className="w-24 h-9 rounded-md bg-border/60 animate-pulse" />
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-3">
            {isLoaded && isSignedIn && <UserButton />}
            <button
              onClick={toggleMenu}
              aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isMenuOpen}
              aria-controls="mobile-nav-menu"
              className="relative flex items-center justify-center w-11 h-11 -mr-2 text-text-muted hover:text-primary active:bg-surface rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <span className="sr-only">Toggle navigation menu</span>
              <Menu
                size={24}
                className={`absolute transition-all duration-200 ${
                  isMenuOpen ? 'opacity-0 rotate-90 scale-75' : 'opacity-100 rotate-0 scale-100'
                }`}
              />
              <X
                size={24}
                className={`absolute transition-all duration-200 ${
                  isMenuOpen ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-75'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div
          id="mobile-nav-menu"
          className={`md:hidden grid transition-[grid-template-rows,opacity] duration-300 ease-out ${
            isMenuOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
          }`}
        >
          <div className="overflow-hidden">
            <div className="border-t border-border px-2 pt-2 pb-4 space-y-1">
              {navItems.map(({ href, label, icon: Icon }, i) => {
                const isActive = pathname === href
                return (
                  <Link
                    key={href}
                    href={href}
                    onClick={closeMenu}
                    aria-current={isActive ? 'page' : undefined}
                    style={{ transitionDelay: isMenuOpen ? `${i * 40}ms` : '0ms' }}
                    className={`flex items-center gap-3 px-3 py-3 rounded-md text-base transition-all duration-200 ${
                      isMenuOpen ? 'translate-y-0 opacity-100' : '-translate-y-1 opacity-0'
                    } ${
                      isActive
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'text-text-muted hover:bg-surface hover:text-primary active:bg-surface'
                    }`}
                  >
                    <Icon size={20} />
                    <span>{label}</span>
                  </Link>
                )
              })}

              {/* Mobile Auth Section */}
              {isLoaded && !isSignedIn && (
                <div className="pt-3 border-t border-border mt-3 space-y-2">
                  <SignInButton mode="modal">
                    <button className="w-full px-3 py-3 text-sm font-medium text-white bg-primary hover:bg-primary/90 active:scale-[0.98] rounded-md transition-all">
                      Sign In
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="w-full px-3 py-3 text-sm font-medium text-primary border border-primary hover:bg-primary/5 active:scale-[0.98] rounded-md transition-all">
                      Sign Up
                    </button>
                  </SignUpButton>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}