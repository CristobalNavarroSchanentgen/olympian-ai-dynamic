import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity,
  Cpu,
  HardDrive,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Gauge,
  Server,
  Database,
  Network,
  Clock,
  RefreshCw
} from 'lucide-react'
import { systemAPI } from '@/lib/api'
import { formatBytes, formatDuration } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

interface SystemResources {
  cpu: {
    count: number
    count_logical: number
    percent: number
    per_cpu: number[]
    frequency?: { current: number; min: number; max: number }
  }
  memory: {
    total: number
    available: number
    used: number
    free: number
    percent: number
    total_gb: number
    available_gb: number
  }
  disk: {
    total: number
    used: number
    free: number
    percent: number
    total_gb: number
    free_gb: number
  }
  network: {
    connections: number
    interfaces: Record<string, any[]>
  }
  gpu: {
    available: boolean
    type: string
    details?: string
  }
}

interface SystemCapacity {
  capacity_scores: {
    cpu: number
    memory: number
    disk: number
    overall: number
  }
  status: 'healthy' | 'constrained' | 'critical'
  recommendations: string[]
  max_concurrent_operations: number
}

interface SystemMetrics {
  metrics: {
    cpu: number[]
    memory: number[]
    timestamp: string[]
  }
  averages: {
    cpu: number
    memory: number
  }
  peaks: {
    cpu: number
    memory: number
  }
}

export default function SystemMonitoring() {
  const [resources, setResources] = useState<SystemResources | null>(null)
  const [capacity, setCapacity] = useState<SystemCapacity | null>(null)
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [processes, setProcesses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchAllData()
    
    if (autoRefresh) {
      const interval = setInterval(fetchAllData, 5000) // Refresh every 5 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const fetchAllData = async () => {
    try {
      const [resourcesRes, capacityRes, metricsRes, processesRes] = await Promise.all([
        systemAPI.getResources(),
        systemAPI.getCapacity(),
        systemAPI.getMetrics(),
        systemAPI.getProcesses()
      ])
      
      setResources(resourcesRes.data)
      setCapacity(capacityRes.data)
      setMetrics(metricsRes.data)
      setProcesses(processesRes.data.processes)
    } catch (error) {
      console.error('Failed to fetch system data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchAllData()
  }

  const handleOptimize = async () => {
    try {
      const response = await systemAPI.optimize()
      toast({
        title: "System Optimized",
        description: `${response.data.optimizations.length} optimizations applied`,
        className: "bg-gradient-to-r from-olympus-gold/20 to-zeus-primary/20 border-olympus-gold"
      })
      fetchAllData()
    } catch (error) {
      console.error('Failed to optimize system:', error)
      toast({
        title: "Optimization Failed",
        description: "Unable to optimize system resources",
        variant: "destructive"
      })
    }
  }

  const getStatusColor = (percent: number) => {
    if (percent < 50) return 'text-green-500'
    if (percent < 80) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-500/10 text-green-500">Healthy</Badge>
      case 'constrained':
        return <Badge className="bg-yellow-500/10 text-yellow-500">Constrained</Badge>
      case 'critical':
        return <Badge className="bg-red-500/10 text-red-500">Critical</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  // Prepare chart data
  const chartData = metrics ? metrics.metrics.timestamp.map((time, index) => ({
    time: new Date(time).toLocaleTimeString(),
    cpu: metrics.metrics.cpu[index],
    memory: metrics.metrics.memory[index]
  })) : []

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-96" />
      </div>
    )
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
          <h1 className="text-3xl font-divine font-bold">System Oracle</h1>
          <p className="text-gray-400 mt-1">Divine computational resource monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Auto-refresh</span>
            <Button
              variant={autoRefresh ? "default" : "outline"}
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? "bg-green-600 hover:bg-green-700" : ""}
            >
              {autoRefresh ? "On" : "Off"}
            </Button>
          </div>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
            className="border-olympus-gold/20"
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button variant="divine" onClick={handleOptimize}>
            <Zap className="h-4 w-4 mr-2" />
            Optimize
          </Button>
        </div>
      </motion.div>

      {/* System Status Overview */}
      {capacity && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>Overall divine computational health</CardDescription>
                </div>
                {getStatusBadge(capacity.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-olympus-gold">{capacity.capacity_scores.overall.toFixed(0)}%</div>
                  <p className="text-sm text-gray-400">Overall Capacity</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold" style={{ color: `hsl(${capacity.capacity_scores.cpu * 1.2}, 70%, 50%)` }}>
                    {capacity.capacity_scores.cpu.toFixed(0)}%
                  </div>
                  <p className="text-sm text-gray-400">CPU Available</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold" style={{ color: `hsl(${capacity.capacity_scores.memory * 1.2}, 70%, 50%)` }}>
                    {capacity.capacity_scores.memory.toFixed(0)}%
                  </div>
                  <p className="text-sm text-gray-400">Memory Available</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold" style={{ color: `hsl(${capacity.capacity_scores.disk * 1.2}, 70%, 50%)` }}>
                    {capacity.capacity_scores.disk.toFixed(0)}%
                  </div>
                  <p className="text-sm text-gray-400">Disk Available</p>
                </div>
              </div>
              
              {capacity.recommendations.length > 0 && (
                <Alert className="border-yellow-500/40 bg-yellow-500/10">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Optimization Recommendations</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      {capacity.recommendations.map((rec, index) => (
                        <li key={index} className="text-sm">{rec}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Resource Cards */}
      {resources && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* CPU Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-5 w-5 text-olympus-gold" />
                    <CardTitle className="text-lg">CPU</CardTitle>
                  </div>
                  <span className={cn("text-2xl font-bold", getStatusColor(resources.cpu.percent))}>
                    {resources.cpu.percent}%
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <Progress 
                  value={resources.cpu.percent} 
                  className="h-2 mb-4"
                  indicatorClassName="bg-gradient-to-r from-olympus-gold to-olympus-gold-dark"
                />
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Cores</span>
                    <span>{resources.cpu.count} ({resources.cpu.count_logical} logical)</span>
                  </div>
                  {resources.cpu.frequency && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Frequency</span>
                      <span>{(resources.cpu.frequency.current / 1000).toFixed(2)} GHz</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Memory Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="h-5 w-5 text-zeus-primary" />
                    <CardTitle className="text-lg">Memory</CardTitle>
                  </div>
                  <span className={cn("text-2xl font-bold", getStatusColor(resources.memory.percent))}>
                    {resources.memory.percent}%
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <Progress 
                  value={resources.memory.percent} 
                  className="h-2 mb-4"
                  indicatorClassName="bg-gradient-to-r from-zeus-primary to-zeus-primary/80"
                />
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total</span>
                    <span>{resources.memory.total_gb.toFixed(2)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Available</span>
                    <span>{resources.memory.available_gb.toFixed(2)} GB</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Disk Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HardDrive className="h-5 w-5 text-olympus-sky" />
                    <CardTitle className="text-lg">Storage</CardTitle>
                  </div>
                  <span className={cn("text-2xl font-bold", getStatusColor(resources.disk.percent))}>
                    {resources.disk.percent}%
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <Progress 
                  value={resources.disk.percent} 
                  className="h-2 mb-4"
                  indicatorClassName="bg-gradient-to-r from-olympus-sky to-olympus-sky-dark"
                />
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total</span>
                    <span>{resources.disk.total_gb.toFixed(2)} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Free</span>
                    <span>{resources.disk.free_gb.toFixed(2)} GB</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Metrics Tabs */}
      <Tabs defaultValue="realtime" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 bg-zeus-dark/50">
          <TabsTrigger value="realtime">Real-time Metrics</TabsTrigger>
          <TabsTrigger value="processes">Processes</TabsTrigger>
          <TabsTrigger value="network">Network</TabsTrigger>
        </TabsList>

        {/* Real-time Metrics Tab */}
        <TabsContent value="realtime">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Real-time Performance</CardTitle>
              <CardDescription>Live system metrics visualization</CardDescription>
            </CardHeader>
            <CardContent>
              {metrics && chartData.length > 0 ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-medium mb-4">CPU & Memory Usage</h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#FFD700" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#FFD700" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4B0082" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#4B0082" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis dataKey="time" stroke="#666" />
                        <YAxis stroke="#666" />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                            border: '1px solid #FFD700',
                            borderRadius: '8px'
                          }} 
                        />
                        <Area 
                          type="monotone" 
                          dataKey="cpu" 
                          stroke="#FFD700" 
                          fillOpacity={1} 
                          fill="url(#cpuGradient)" 
                          name="CPU %"
                        />
                        <Area 
                          type="monotone" 
                          dataKey="memory" 
                          stroke="#4B0082" 
                          fillOpacity={1} 
                          fill="url(#memoryGradient)" 
                          name="Memory %"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 rounded-lg bg-olympus-gold/5 border border-olympus-gold/10">
                      <p className="text-sm text-gray-400 mb-1">Average CPU</p>
                      <p className="text-2xl font-bold text-olympus-gold">{metrics.averages.cpu}%</p>
                      <p className="text-xs text-gray-500 mt-1">Peak: {metrics.peaks.cpu}%</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-zeus-primary/5 border border-zeus-primary/10">
                      <p className="text-sm text-gray-400 mb-1">Average Memory</p>
                      <p className="text-2xl font-bold text-zeus-primary">{metrics.averages.memory}%</p>
                      <p className="text-xs text-gray-500 mt-1">Peak: {metrics.peaks.memory}%</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <p className="text-gray-400">No metrics data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processes Tab */}
        <TabsContent value="processes">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Active Processes</CardTitle>
              <CardDescription>Divine computational tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {processes.map((proc, index) => (
                  <motion.div
                    key={proc.pid}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-zeus-dark/30 border border-zeus-dark/50"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium">{proc.name}</p>
                      <p className="text-xs text-gray-400">PID: {proc.pid}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm">CPU: {proc.cpu_percent}%</p>
                        <p className="text-xs text-gray-400">Mem: {proc.memory_percent.toFixed(1)}%</p>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {formatDuration(proc.uptime)}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Network Tab */}
        <TabsContent value="network">
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <CardTitle>Network Interfaces</CardTitle>
              <CardDescription>Divine connection pathways</CardDescription>
            </CardHeader>
            <CardContent>
              {resources && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-lg bg-olympus-sky/5 border border-olympus-sky/10">
                    <div className="flex items-center gap-3">
                      <Network className="h-5 w-5 text-olympus-sky" />
                      <span className="font-medium">Active Connections</span>
                    </div>
                    <Badge variant="secondary" className="text-lg">
                      {resources.network.connections}
                    </Badge>
                  </div>
                  
                  <div className="space-y-2">
                    {Object.entries(resources.network.interfaces).map(([name, addrs]) => (
                      <div key={name} className="p-3 rounded-lg bg-zeus-dark/30 border border-zeus-dark/50">
                        <p className="text-sm font-medium mb-2">{name}</p>
                        <div className="space-y-1">
                          {addrs.map((addr: any, index: number) => (
                            <p key={index} className="text-xs text-gray-400">
                              {addr.family}: {addr.address}
                            </p>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* GPU Status */}
      {resources?.gpu.available && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-green-500" />
                  <CardTitle>GPU Status</CardTitle>
                </div>
                <Badge className="bg-green-500/10 text-green-500">Active</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm">
                Type: <span className="font-medium">{resources.gpu.type}</span>
              </p>
              {resources.gpu.details && (
                <p className="text-xs text-gray-400 mt-2">{resources.gpu.details}</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}