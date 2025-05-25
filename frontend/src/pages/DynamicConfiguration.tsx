import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  RefreshCw,
  Search,
  Plus,
  Trash2,
  Settings,
  Cloud,
  GitBranch,
  Webhook,
  Database,
  Check,
  X,
  AlertCircle,
  Zap,
  Shield,
  Globe
} from 'lucide-react'
import { useConfig } from '@/contexts/ConfigContext'
import { discoveryAPI, configAPI } from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

interface ServiceStatus {
  type: string
  name: string
  endpoint?: string
  status: 'connected' | 'disconnected' | 'error'
  details?: any
}

export default function DynamicConfiguration() {
  const { 
    discoveredServices, 
    userPreferences, 
    isLoading, 
    triggerDiscovery, 
    updatePreferences,
    refreshConfig 
  } = useConfig()
  const { toast } = useToast()
  
  const [scanning, setScanning] = useState(false)
  const [serviceStatuses, setServiceStatuses] = useState<ServiceStatus[]>([])
  const [customEndpoint, setCustomEndpoint] = useState('')
  const [preferences, setPreferences] = useState(userPreferences)

  useEffect(() => {
    setPreferences(userPreferences)
  }, [userPreferences])

  useEffect(() => {
    buildServiceStatuses()
  }, [discoveredServices])

  const buildServiceStatuses = () => {
    const statuses: ServiceStatus[] = []
    
    // Ollama services
    discoveredServices.ollama?.endpoints?.forEach(endpoint => {
      statuses.push({
        type: 'ollama',
        name: 'Ollama Oracle',
        endpoint,
        status: 'connected',
        details: {
          models: discoveredServices.ollama.models?.filter(m => m.endpoint === endpoint).length || 0
        }
      })
    })
    
    // MCP servers
    discoveredServices.mcp_servers?.configured?.forEach(server => {
      statuses.push({
        type: 'mcp',
        name: `MCP ${server.type}`,
        endpoint: server.endpoint,
        status: 'connected',
        details: {
          tools: server.tools?.length || 0
        }
      })
    })
    
    // Webhooks
    discoveredServices.webhooks?.endpoints?.forEach(webhook => {
      statuses.push({
        type: 'webhook',
        name: `Webhook ${webhook.type}`,
        endpoint: webhook.url,
        status: webhook.configured ? 'connected' : 'disconnected'
      })
    })
    
    setServiceStatuses(statuses)
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await triggerDiscovery()
      toast({
        title: "Discovery Started",
        description: "Scanning for divine services across the realm...",
        className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold"
      })
      
      // Refresh after a delay to get results
      setTimeout(async () => {
        await refreshConfig()
        setScanning(false)
      }, 5000)
    } catch (error) {
      console.error('Failed to trigger discovery:', error)
      setScanning(false)
      toast({
        title: "Discovery Failed",
        description: "Unable to summon the discovery oracle",
        variant: "destructive"
      })
    }
  }

  const addCustomEndpoint = async () => {
    if (!customEndpoint) return
    
    try {
      const newPreferences = {
        ...preferences,
        custom_endpoints: [...(preferences.custom_endpoints || []), customEndpoint]
      }
      await updatePreferences(newPreferences)
      setCustomEndpoint('')
      toast({
        title: "Endpoint Added",
        description: "Custom divine endpoint has been registered"
      })
    } catch (error) {
      console.error('Failed to add endpoint:', error)
    }
  }

  const removeCustomEndpoint = async (endpoint: string) => {
    try {
      const newPreferences = {
        ...preferences,
        custom_endpoints: preferences.custom_endpoints?.filter(e => e !== endpoint) || []
      }
      await updatePreferences(newPreferences)
    } catch (error) {
      console.error('Failed to remove endpoint:', error)
    }
  }

  const toggleService = async (serviceId: string) => {
    const isDisabled = preferences.disabled_services?.includes(serviceId) || false
    const newDisabledServices = isDisabled
      ? preferences.disabled_services?.filter(s => s !== serviceId) || []
      : [...(preferences.disabled_services || []), serviceId]
    
    try {
      await updatePreferences({
        ...preferences,
        disabled_services: newDisabledServices
      })
    } catch (error) {
      console.error('Failed to toggle service:', error)
    }
  }

  const getServiceIcon = (type: string) => {
    switch (type) {
      case 'ollama': return Cloud
      case 'mcp': return GitBranch
      case 'webhook': return Webhook
      case 'redis': return Database
      default: return Settings
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-500'
      case 'disconnected': return 'text-gray-500'
      case 'error': return 'text-red-500'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-divine font-bold">Divine Configuration</h1>
          <p className="text-gray-400 mt-1">Dynamic service discovery and configuration</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={refreshConfig}
            disabled={isLoading}
            className="border-olympus-gold/20"
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
          <Button
            variant="divine"
            onClick={handleScan}
            disabled={scanning}
          >
            <Search className={cn("h-4 w-4 mr-2", scanning && "animate-pulse")} />
            {scanning ? 'Scanning...' : 'Discover Services'}
          </Button>
        </div>
      </motion.div>

      {/* Discovery Status */}
      {scanning && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Alert className="border-olympus-gold/40 bg-olympus-gold/10">
            <Zap className="h-4 w-4 animate-pulse" />
            <AlertTitle>Divine Discovery in Progress</AlertTitle>
            <AlertDescription>
              The oracles are searching for services across the digital realm...
            </AlertDescription>
          </Alert>
        </motion.div>
      )}

      {/* Service Tabs */}
      <Tabs defaultValue="services" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 bg-zeus-dark/50">
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        {/* Services Tab */}
        <TabsContent value="services">
          <div className="grid gap-4">
            {/* Service Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-32" />
                ))
              ) : (
                serviceStatuses.map((service, index) => {
                  const Icon = getServiceIcon(service.type)
                  const isDisabled = preferences.disabled_services?.includes(service.endpoint || service.name) || false
                  
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur divine-card">
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <div className={cn(
                                "p-2 rounded-lg",
                                service.status === 'connected' ? 'bg-green-500/10' : 'bg-gray-500/10'
                              )}>
                                <Icon className={cn("h-5 w-5", getStatusColor(service.status))} />
                              </div>
                              <div>
                                <CardTitle className="text-sm">{service.name}</CardTitle>
                                {service.endpoint && (
                                  <p className="text-xs text-gray-400 mt-1">{service.endpoint}</p>
                                )}
                              </div>
                            </div>
                            <Switch
                              checked={!isDisabled}
                              onCheckedChange={() => toggleService(service.endpoint || service.name)}
                            />
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="flex items-center justify-between">
                            <Badge 
                              variant="secondary" 
                              className={cn(
                                "text-xs",
                                service.status === 'connected' && "bg-green-500/10 text-green-500",
                                service.status === 'error' && "bg-red-500/10 text-red-500"
                              )}
                            >
                              {service.status === 'connected' ? (
                                <Check className="h-3 w-3 mr-1" />
                              ) : service.status === 'error' ? (
                                <X className="h-3 w-3 mr-1" />
                              ) : (
                                <AlertCircle className="h-3 w-3 mr-1" />
                              )}
                              {service.status}
                            </Badge>
                            {service.details && (
                              <div className="text-xs text-gray-400">
                                {service.details.models && `${service.details.models} models`}
                                {service.details.tools && `${service.details.tools} tools`}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  )
                })
              )}
            </div>

            {/* Add Custom Service */}
            <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
              <CardHeader>
                <CardTitle>Add Custom Service</CardTitle>
                <CardDescription>Manually register a divine service endpoint</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Input
                    value={customEndpoint}
                    onChange={(e) => setCustomEndpoint(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="flex-1 border-olympus-gold/20"
                  />
                  <Button
                    variant="divine"
                    onClick={addCustomEndpoint}
                    disabled={!customEndpoint}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Endpoint
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Endpoints Tab */}
        <TabsContent value="endpoints">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Service Endpoints</CardTitle>
              <CardDescription>All discovered and custom endpoints</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Ollama Endpoints */}
                <div>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-olympus-gold" />
                    Ollama Endpoints
                  </h4>
                  <div className="space-y-2">
                    {discoveredServices.ollama?.endpoints?.map((endpoint, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-olympus-gold/5 border border-olympus-gold/10">
                        <span className="text-sm font-mono">{endpoint}</span>
                        <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                          Active
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Custom Endpoints */}
                {preferences.custom_endpoints && preferences.custom_endpoints.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                      <Globe className="h-4 w-4 text-zeus-primary" />
                      Custom Endpoints
                    </h4>
                    <div className="space-y-2">
                      {preferences.custom_endpoints.map((endpoint, index) => (
                        <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-zeus-primary/5 border border-zeus-primary/10">
                          <span className="text-sm font-mono">{endpoint}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeCustomEndpoint(endpoint)}
                            className="text-red-500 hover:text-red-400"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>User Preferences</CardTitle>
              <CardDescription>Customize your divine experience</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-sm mb-2">Preferred Models</Label>
                <div className="space-y-2">
                  {discoveredServices.ollama?.models?.slice(0, 5).map((model) => (
                    <div key={model.name} className="flex items-center gap-2">
                      <Switch
                        checked={preferences.preferred_models?.includes(model.name) || false}
                        onCheckedChange={(checked) => {
                          const newModels = checked
                            ? [...(preferences.preferred_models || []), model.name]
                            : preferences.preferred_models?.filter(m => m !== model.name) || []
                          updatePreferences({ ...preferences, preferred_models: newModels })
                        }}
                      />
                      <Label className="text-sm font-normal">{model.name}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-sm mb-2">Discovery Settings</Label>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-normal">Auto-discovery on startup</Label>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-normal">Show discovery notifications</Label>
                    <Switch defaultChecked />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>Divine protection for your realm</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Alert className="border-zeus-primary/40 bg-zeus-primary/10">
                <Shield className="h-4 w-4" />
                <AlertTitle>Divine Shield Active</AlertTitle>
                <AlertDescription>
                  All connections are secured with divine encryption and authentication
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div>
                  <Label className="text-sm mb-2">API Keys</Label>
                  <div className="space-y-2">
                    <Input
                      type="password"
                      placeholder="Enter API key..."
                      className="border-olympus-gold/20"
                    />
                    <Button variant="outline" className="w-full">
                      <Plus className="h-4 w-4 mr-2" />
                      Add API Key
                    </Button>
                  </div>
                </div>

                <div>
                  <Label className="text-sm mb-2">Security Options</Label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-normal">Enable rate limiting</Label>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-normal">Verify webhook signatures</Label>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-normal">Auto-rotate secrets</Label>
                      <Switch />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}