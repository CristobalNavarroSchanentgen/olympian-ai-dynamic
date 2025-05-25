import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import { useToast } from '@/components/ui/use-toast'

interface WebSocketMessage {
  type: string
  data?: any
  timestamp?: string
  [key: string]: any
}

interface WebSocketContextType {
  socket: WebSocket | null
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  sendMessage: (message: WebSocketMessage) => void
  lastMessage: WebSocketMessage | null
  subscribe: (type: string, handler: (message: WebSocketMessage) => void) => () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<WebSocketContextType['connectionStatus']>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const { toast } = useToast()
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000
  
  const messageHandlersRef = useRef<Map<string, Set<(message: WebSocketMessage) => void>>>(new Map())

  const connect = useCallback(() => {
    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('⚡ Divine connection established')
        setConnectionStatus('connected')
        setSocket(ws)
        reconnectAttemptsRef.current = 0
        
        toast({
          title: "Connected to Olympus",
          description: "The divine connection has been established.",
          className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold",
        })
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(message)
          
          // Notify all subscribers for this message type
          const handlers = messageHandlersRef.current.get(message.type)
          if (handlers) {
            handlers.forEach(handler => handler(message))
          }
          
          // Also notify global handlers
          const globalHandlers = messageHandlersRef.current.get('*')
          if (globalHandlers) {
            globalHandlers.forEach(handler => handler(message))
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('error')
      }
      
      ws.onclose = () => {
        console.log('🌙 Divine connection closed')
        setConnectionStatus('disconnected')
        setSocket(null)
        
        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          
          toast({
            title: "Connection Lost",
            description: `Attempting to reconnect... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`,
            variant: "destructive",
          })
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionStatus('connecting')
            connect()
          }, reconnectDelay)
        } else {
          toast({
            title: "Connection Failed",
            description: "Unable to establish divine connection. Please refresh the page.",
            variant: "destructive",
          })
        }
      }
      
      setConnectionStatus('connecting')
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setConnectionStatus('error')
    }
  }, [toast])

  useEffect(() => {
    connect()
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (socket) {
        socket.close()
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
      toast({
        title: "Connection Error",
        description: "Unable to send message. Please check your connection.",
        variant: "destructive",
      })
    }
  }, [socket, toast])

  const subscribe = useCallback((type: string, handler: (message: WebSocketMessage) => void) => {
    if (!messageHandlersRef.current.has(type)) {
      messageHandlersRef.current.set(type, new Set())
    }
    messageHandlersRef.current.get(type)!.add(handler)
    
    // Return unsubscribe function
    return () => {
      const handlers = messageHandlersRef.current.get(type)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(type)
        }
      }
    }
  }, [])

  return (
    <WebSocketContext.Provider
      value={{
        socket,
        connectionStatus,
        sendMessage,
        lastMessage,
        subscribe,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}