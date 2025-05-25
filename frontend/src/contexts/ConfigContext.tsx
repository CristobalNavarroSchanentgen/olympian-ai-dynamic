import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useWebSocket } from './WebSocketContext'
import api from '@/lib/api'

interface DiscoveredService {
  endpoints: string[]
  models?: any[]
  capabilities?: Record<string, any>
  available?: any[]
  configured?: any[]
  available_types?: string[]
}

interface DiscoveredServices {
  ollama: DiscoveredService
  mcp_servers: DiscoveredService
  webhooks: DiscoveredService
  [key: string]: DiscoveredService
}

interface UserPreferences {
  preferred_models: string[]
  custom_endpoints: string[]
  manual_overrides: Record<string, any>
  disabled_services: string[]
}

interface ConfigContextType {
  discoveredServices: DiscoveredServices
  userPreferences: UserPreferences
  activeServices: Record<string, any>
  isLoading: boolean
  error: string | null
  refreshConfig: () => Promise<void>
  updatePreferences: (preferences: Partial<UserPreferences>) => Promise<void>
  triggerDiscovery: () => Promise<void>
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined)

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [discoveredServices, setDiscoveredServices] = useState<DiscoveredServices>({
    ollama: { endpoints: [], models: [], capabilities: {} },
    mcp_servers: { available: [], configured: [] },
    webhooks: { available_types: [], endpoints: [] },
  })
  const [userPreferences, setUserPreferences] = useState<UserPreferences>({
    preferred_models: [],
    custom_endpoints: [],
    manual_overrides: {},
    disabled_services: [],
  })
  const [activeServices, setActiveServices] = useState<Record<string, any>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const { subscribe } = useWebSocket()

  const fetchConfig = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await api.get('/config/dynamic')
      const data = response.data
      
      setDiscoveredServices(data.discovered_services || {})
      setUserPreferences(data.user_preferences || {})
      setActiveServices(data.active_services || {})
    } catch (err) {
      console.error('Failed to fetch configuration:', err)
      setError('Failed to load configuration')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const refreshConfig = useCallback(async () => {
    await fetchConfig()
  }, [fetchConfig])

  const updatePreferences = useCallback(async (preferences: Partial<UserPreferences>) => {
    try {
      const response = await api.put('/config/preferences', preferences)
      setUserPreferences(response.data.preferences)
    } catch (err) {
      console.error('Failed to update preferences:', err)
      throw err
    }
  }, [])

  const triggerDiscovery = useCallback(async () => {
    try {
      await api.get('/discovery/scan')
      // The scan runs in background, we'll get updates via WebSocket
    } catch (err) {
      console.error('Failed to trigger discovery:', err)
      throw err
    }
  }, [])

  // Subscribe to configuration updates via WebSocket
  useEffect(() => {
    const unsubscribeWelcome = subscribe('welcome', (message) => {
      if (message.config) {
        setDiscoveredServices(message.config.discovered_services || {})
        setUserPreferences(message.config.user_preferences || {})
        setActiveServices(message.config.active_services || {})
        setIsLoading(false)
      }
    })

    const unsubscribeConfigUpdate = subscribe('config_updated', (message) => {
      fetchConfig() // Refresh entire config when something changes
    })

    const unsubscribeServiceUpdate = subscribe('service_update', (message) => {
      if (message.details) {
        setDiscoveredServices(prev => ({
          ...prev,
          [message.service_type]: message.details,
        }))
      }
    })

    const unsubscribeDiscoveredServices = subscribe('discovered_services', (message) => {
      if (message.data) {
        setDiscoveredServices(message.data)
      }
    })

    // Initial fetch
    fetchConfig()

    return () => {
      unsubscribeWelcome()
      unsubscribeConfigUpdate()
      unsubscribeServiceUpdate()
      unsubscribeDiscoveredServices()
    }
  }, [subscribe, fetchConfig])

  return (
    <ConfigContext.Provider
      value={{
        discoveredServices,
        userPreferences,
        activeServices,
        isLoading,
        error,
        refreshConfig,
        updatePreferences,
        triggerDiscovery,
      }}
    >
      {children}
    </ConfigContext.Provider>
  )
}

export function useConfig() {
  const context = useContext(ConfigContext)
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider')
  }
  return context
}