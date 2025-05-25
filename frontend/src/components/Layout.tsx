import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Zap,
  MessageSquare,
  FolderOpen,
  Settings,
  Activity,
  Menu,
  X,
  Cloud,
  Sparkles,
  Shield,
  ChevronRight
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { ModeToggle } from './mode-toggle'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Zap },
  { name: 'Divine Dialogue', href: '/chat', icon: MessageSquare },
  { name: 'Sacred Projects', href: '/projects', icon: FolderOpen },
  { name: 'Divine Config', href: '/config', icon: Settings },
  { name: 'System Oracle', href: '/system', icon: Activity },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()
  const { connectionStatus } = useWebSocket()

  return (
    <div className="min-h-screen bg-gradient-to-br from-zeus-dark via-gray-900 to-zeus-dark">
      {/* Divine Header */}
      <header className="fixed top-0 z-50 w-full border-b border-olympus-gold/20 bg-zeus-dark/80 backdrop-blur-xl">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="rounded-lg p-2 hover:bg-olympus-gold/10 transition-colors"
            >
              {sidebarOpen ? <X className="h-5 w-5 text-olympus-gold" /> : <Menu className="h-5 w-5 text-olympus-gold" />}
            </button>
            
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative">
                <Zap className="h-8 w-8 text-olympus-gold animate-pulse-slow" />
                <div className="absolute inset-0 bg-olympus-gold/20 blur-xl animate-pulse-slow" />
              </div>
              <h1 className="text-2xl font-divine font-bold bg-gradient-to-r from-olympus-gold to-olympus-gold-light bg-clip-text text-transparent group-hover:from-olympus-gold-light group-hover:to-olympus-gold transition-all duration-300">
                Olympian AI
              </h1>
            </Link>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              <div className={cn(
                "h-2 w-2 rounded-full",
                connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' : 
                connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                'bg-red-500'
              )} />
              <span className="text-sm text-gray-400">
                {connectionStatus === 'connected' ? 'Divine Connection' : 
                 connectionStatus === 'connecting' ? 'Summoning...' :
                 'Mortal Realm'}
              </span>
            </div>

            <ModeToggle />

            {/* Divine Status Icons */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-olympus-gold/10 border border-olympus-gold/20">
              <Cloud className="h-4 w-4 text-olympus-sky" />
              <Sparkles className="h-4 w-4 text-olympus-gold" />
              <Shield className="h-4 w-4 text-zeus-primary" />
            </div>
          </div>
        </div>
      </header>

      <div className="flex pt-16">
        {/* Divine Sidebar */}
        <motion.aside
          initial={{ x: 0 }}
          animate={{ x: sidebarOpen ? 0 : -280 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed left-0 z-40 h-[calc(100vh-4rem)] w-64 border-r border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur-xl"
        >
          <nav className="flex flex-col gap-1 p-4">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                             (item.href !== '/' && location.pathname.startsWith(item.href))
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-gradient-to-r from-olympus-gold/20 to-olympus-gold/10 text-olympus-gold shadow-divine"
                      : "text-gray-400 hover:bg-olympus-gold/5 hover:text-olympus-gold-light"
                  )}
                >
                  <item.icon className={cn(
                    "h-5 w-5 transition-transform group-hover:scale-110",
                    isActive && "animate-pulse-slow"
                  )} />
                  <span>{item.name}</span>
                  {isActive && (
                    <ChevronRight className="ml-auto h-4 w-4 animate-pulse" />
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Divine Quote */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="rounded-lg bg-gradient-to-r from-zeus-primary/10 to-olympus-gold/10 p-4 border border-olympus-gold/20">
              <p className="text-xs text-gray-400 italic font-ancient">
                "With divine wisdom and mortal ingenuity, we forge the future."
              </p>
              <p className="text-xs text-olympus-gold mt-2">- The Oracle</p>
            </div>
          </div>
        </motion.aside>

        {/* Main Content */}
        <main className={cn(
          "flex-1 transition-all duration-300",
          sidebarOpen ? "ml-64" : "ml-0"
        )}>
          <div className="min-h-[calc(100vh-4rem)] p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}