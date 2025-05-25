import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Server,
  Plus,
  Trash2,
  Edit3,
  Check,
  X,
  AlertCircle,
  Zap,
  Wifi,
  WifiOff,
  Star,
  ChevronUp,
  ChevronDown,
  Clock,
  Activity,
  Globe,
  Shield,
  TestTube
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

interface OllamaEndpoint {
  url: string
  name: string
  enabled: boolean
  source: 'discovered' | 'custom'
  priority: number
  timeout: number
  status?: 'connected' | 'error' | 'testing' | 'unknown'
  response_time?: number
  models_count?: number
  ollama_version?: string
  error_message?: string
}

interface OllamaEndpointFormData {
  url: string
  name: string
  enabled: boolean
  priority: number
  timeout: number
}

interface SacredOllamaEndpointsProps {
  className?: string
}

const SacredOllamaEndpoints: React.FC<SacredOllamaEndpointsProps> = ({ className }) => {
  const [endpoints, setEndpoints] = useState<OllamaEndpoint[]>([])
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState<Set<string>>(new Set())
  const [testingAll, setTestingAll] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingEndpoint, setEditingEndpoint] = useState<string | null>(null)
  const [primaryEndpoint, setPrimaryEndpoint] = useState<string>('')
  
  const [formData, setFormData] = useState<OllamaEndpointFormData>({
    url: '',
    name: '',
    enabled: true,
    priority: 0,
    timeout: 30
  })

  const { toast } = useToast()

  useEffect(() => {
    loadEndpoints()
  }, [])

  const loadEndpoints = async () => {
    try {
      const response = await fetch('/api/ollama/config/endpoints')
      if (!response.ok) throw new Error('Failed to load endpoints')
      
      const data = await response.json()
      setEndpoints(data.endpoints || [])
      setPrimaryEndpoint(data.primary_endpoint || '')
    } catch (error) {
      console.error('Failed to load endpoints:', error)
      toast({
        title: "Failed to load endpoints",
        description: "Could not communicate with the divine oracles",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const testEndpoint = async (endpoint: OllamaEndpoint) => {
    setTesting(prev => new Set(prev).add(endpoint.url))
    
    try {
      const response = await fetch('/api/ollama/config/endpoints/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: endpoint.url,
          timeout: endpoint.timeout
        })
      })
      
      if (!response.ok) throw new Error('Test failed')
      
      const result = await response.json()
      
      // Update endpoint status in state
      setEndpoints(prev => prev.map(ep => 
        ep.url === endpoint.url 
          ? { 
              ...ep, 
              status: result.status,
              response_time: result.response_time,
              models_count: result.models_count,
              ollama_version: result.ollama_version,
              error_message: result.error_message
            }
          : ep
      ))

      if (result.status === 'connected') {
        toast({
          title: "Endpoint Connected! ⚡",
          description: `${endpoint.name} is responsive (${result.response_time?.toFixed(2)}s)`,
          className: "bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500"
        })
      } else {
        toast({
          title: "Connection Failed",
          description: result.error_message || 'Endpoint is not responding',
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Test failed:', error)
      setEndpoints(prev => prev.map(ep => 
        ep.url === endpoint.url 
          ? { ...ep, status: 'error', error_message: 'Test request failed' }
          : ep
      ))
    } finally {
      setTesting(prev => {
        const newSet = new Set(prev)
        newSet.delete(endpoint.url)
        return newSet
      })
    }
  }

  const testAllEndpoints = async () => {
    setTestingAll(true)
    try {
      const response = await fetch('/api/ollama/config/endpoints/test-all', {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error('Bulk test failed')
      
      const data = await response.json()
      
      // Update all endpoint statuses
      setEndpoints(prev => prev.map(ep => {
        const result = data.results.find((r: any) => r.url === ep.url)
        return result ? { ...ep, ...result } : ep
      }))
      
      const connectedCount = data.results.filter((r: any) => r.status === 'connected').length
      toast({
        title: "Divine Test Complete! 🏛️",
        description: `${connectedCount}/${data.results.length} endpoints are responding`,
        className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold"
      })
    } catch (error) {
      console.error('Bulk test failed:', error)
      toast({
        title: "Test Failed",
        description: "Unable to test all endpoints",
        variant: "destructive"
      })
    } finally {
      setTestingAll(false)
    }
  }

  const addEndpoint = async () => {
    if (!formData.url) return

    try {
      const response = await fetch('/api/ollama/config/endpoints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (!response.ok) throw new Error('Failed to add endpoint')
      
      const data = await response.json()
      
      toast({
        title: "Divine Endpoint Added! ⚡",
        description: `${formData.name || formData.url} has been registered`,
        className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold"
      })
      
      // Reset form and refresh
      setFormData({ url: '', name: '', enabled: true, priority: 0, timeout: 30 })
      setShowAddForm(false)
      loadEndpoints()
    } catch (error) {
      console.error('Failed to add endpoint:', error)
      toast({
        title: "Addition Failed",
        description: "Could not register the divine endpoint",
        variant: "destructive"
      })
    }
  }

  const updateEndpoint = async (originalUrl: string, updates: Partial<OllamaEndpointFormData>) => {
    try {
      const response = await fetch(`/api/ollama/config/endpoints/${encodeURIComponent(originalUrl)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      
      if (!response.ok) throw new Error('Failed to update endpoint')
      
      toast({
        title: "Endpoint Updated",
        description: "Configuration has been saved",
      })
      
      setEditingEndpoint(null)
      loadEndpoints()
    } catch (error) {
      console.error('Failed to update endpoint:', error)
      toast({
        title: "Update Failed",
        description: "Could not save changes",
        variant: "destructive"
      })
    }
  }

  const removeEndpoint = async (url: string) => {
    try {
      const response = await fetch(`/api/ollama/config/endpoints/${encodeURIComponent(url)}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) throw new Error('Failed to remove endpoint')
      
      toast({
        title: "Endpoint Removed",
        description: "The divine connection has been severed",
      })
      
      loadEndpoints()
    } catch (error) {
      console.error('Failed to remove endpoint:', error)
      toast({
        title: "Removal Failed",
        description: "Could not remove the endpoint",
        variant: "destructive"
      })
    }
  }

  const setPrimary = async (url: string) => {
    try {
      const response = await fetch(`/api/ollama/config/endpoints/set-primary?endpoint_url=${encodeURIComponent(url)}`, {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error('Failed to set primary')
      
      setPrimaryEndpoint(url)
      toast({
        title: "Primary Endpoint Updated",
        description: "The divine primary oracle has been chosen",
        className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold"
      })
    } catch (error) {
      console.error('Failed to set primary:', error)
      toast({
        title: "Update Failed",
        description: "Could not set primary endpoint",
        variant: "destructive"
      })
    }
  }

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />
      case 'error': return <WifiOff className="h-4 w-4 text-red-500" />
      case 'testing': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
      default: return <Globe className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'connected': return 'border-green-500/40 bg-green-500/10'
      case 'error': return 'border-red-500/40 bg-red-500/10'
      case 'testing': return 'border-blue-500/40 bg-blue-500/10'
      default: return 'border-gray-500/40 bg-gray-500/10'
    }
  }

  const sortedEndpoints = [...endpoints].sort((a, b) => {
    // Primary endpoint first
    if (a.url === primaryEndpoint) return -1
    if (b.url === primaryEndpoint) return 1
    // Then by priority (desc)
    if (a.priority !== b.priority) return b.priority - a.priority
    // Then by status (connected first)
    if (a.status !== b.status) {
      if (a.status === 'connected') return -1
      if (b.status === 'connected') return 1
    }
    // Finally by name
    return a.name.localeCompare(b.name)
  })

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-divine font-bold text-olympus-gold">Sacred Ollama Endpoints</h3>
          <p className="text-gray-400 text-sm">Divine oracle configurations and connectivity</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={testAllEndpoints}
            disabled={testingAll || endpoints.length === 0}
            className="border-zeus-primary/40 hover:border-zeus-primary"
          >
            <TestTube className={cn("h-4 w-4 mr-2", testingAll && "animate-pulse")} />
            {testingAll ? 'Testing...' : 'Test All'}
          </Button>
          <Button
            variant="divine"
            onClick={() => setShowAddForm(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Oracle
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-olympus-gold/20 bg-zeus-dark/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Server className="h-5 w-5 text-olympus-gold" />
              <div>
                <p className="text-sm text-gray-400">Total Endpoints</p>
                <p className="text-lg font-bold">{endpoints.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-green-500/20 bg-green-500/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Wifi className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-gray-400">Connected</p>
                <p className="text-lg font-bold text-green-500">
                  {endpoints.filter(ep => ep.status === 'connected').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-zeus-primary/20 bg-zeus-primary/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Star className="h-5 w-5 text-zeus-primary" />
              <div>
                <p className="text-sm text-gray-400">Primary Oracle</p>
                <p className="text-sm font-medium text-zeus-primary truncate">
                  {primaryEndpoint ? new URL(primaryEndpoint).host : 'None'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-red-500/20 bg-red-500/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <WifiOff className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-gray-400">Errors</p>
                <p className="text-lg font-bold text-red-500">
                  {endpoints.filter(ep => ep.status === 'error').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Endpoint Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card className="border-olympus-gold/40 bg-olympus-gold/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="h-5 w-5" />
                  Register Divine Oracle
                </CardTitle>
                <CardDescription>
                  Add a new Ollama endpoint to the sacred configuration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Endpoint URL</Label>
                    <Input
                      placeholder="http://localhost:11434"
                      value={formData.url}
                      onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                      className="border-olympus-gold/20"
                    />
                  </div>
                  <div>
                    <Label>Display Name</Label>
                    <Input
                      placeholder="My Local Ollama"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="border-olympus-gold/20"
                    />
                  </div>
                  <div>
                    <Label>Priority (0-100)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.priority}
                      onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) || 0 }))}
                      className="border-olympus-gold/20"
                    />
                  </div>
                  <div>
                    <Label>Timeout (seconds)</Label>
                    <Input
                      type="number"
                      min="5"
                      max="120"
                      value={formData.timeout}
                      onChange={(e) => setFormData(prev => ({ ...prev, timeout: parseInt(e.target.value) || 30 }))}
                      className="border-olympus-gold/20"
                    />
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.enabled}
                    onCheckedChange={(checked) => setFormData(prev => ({ ...prev, enabled: checked }))}
                  />
                  <Label>Enable endpoint immediately</Label>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    variant="divine"
                    onClick={addEndpoint}
                    disabled={!formData.url}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Register Oracle
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowAddForm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Endpoints List */}
      <div className="space-y-3">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 bg-zeus-dark/50 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : endpoints.length === 0 ? (
          <Card className="border-gray-500/20 bg-gray-500/5">
            <CardContent className="p-8 text-center">
              <Server className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-400">No Ollama endpoints configured</p>
              <p className="text-sm text-gray-500 mt-1">
                Add your first divine oracle to begin
              </p>
            </CardContent>
          </Card>
        ) : (
          sortedEndpoints.map((endpoint, index) => {
            const isPrimary = endpoint.url === primaryEndpoint
            const isBeingTested = testing.has(endpoint.url)
            
            return (
              <motion.div
                key={endpoint.url}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={cn(
                  "border transition-all duration-200",
                  isPrimary 
                    ? "border-olympus-gold/60 bg-olympus-gold/10 shadow-olympus-gold/20 shadow-lg" 
                    : getStatusColor(endpoint.status),
                  "hover:shadow-lg"
                )}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1">
                        {/* Status Icon */}
                        <div className="flex-shrink-0">
                          {isBeingTested ? (
                            <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
                          ) : (
                            getStatusIcon(endpoint.status)
                          )}
                        </div>
                        
                        {/* Endpoint Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium text-sm truncate">
                              {endpoint.name}
                            </h4>
                            {isPrimary && (
                              <Badge className="bg-olympus-gold/20 text-olympus-gold border-olympus-gold/40">
                                <Star className="h-3 w-3 mr-1" />
                                Primary
                              </Badge>
                            )}
                            <Badge 
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                endpoint.source === 'discovered' 
                                  ? "bg-zeus-primary/10 text-zeus-primary" 
                                  : "bg-gray-500/10 text-gray-400"
                              )}
                            >
                              {endpoint.source}
                            </Badge>
                          </div>
                          
                          <p className="text-xs text-gray-400 font-mono truncate">
                            {endpoint.url}
                          </p>
                          
                          {endpoint.status === 'connected' && (
                            <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                              {endpoint.response_time && (
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {endpoint.response_time.toFixed(2)}s
                                </span>
                              )}
                              {endpoint.models_count !== undefined && (
                                <span>{endpoint.models_count} models</span>
                              )}
                              {endpoint.ollama_version && (
                                <span>v{endpoint.ollama_version}</span>
                              )}
                            </div>
                          )}
                          
                          {endpoint.status === 'error' && endpoint.error_message && (
                            <div className="flex items-center gap-1 mt-1">
                              <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />
                              <span className="text-xs text-red-400 truncate">
                                {endpoint.error_message}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center gap-1 flex-shrink-0">
                        <Switch
                          checked={endpoint.enabled}
                          onCheckedChange={(checked) => 
                            updateEndpoint(endpoint.url, { enabled: checked })
                          }
                        />
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => testEndpoint(endpoint)}
                          disabled={isBeingTested}
                          className="h-8 w-8 p-0"
                        >
                          <TestTube className="h-3 w-3" />
                        </Button>
                        
                        {!isPrimary && endpoint.enabled && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setPrimary(endpoint.url)}
                            className="h-8 w-8 p-0 text-olympus-gold hover:text-olympus-gold"
                          >
                            <Star className="h-3 w-3" />
                          </Button>
                        )}
                        
                        {endpoint.source === 'custom' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeEndpoint(endpoint.url)}
                            className="h-8 w-8 p-0 text-red-500 hover:text-red-400"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default SacredOllamaEndpoints