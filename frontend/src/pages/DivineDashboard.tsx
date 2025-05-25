import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Zap, 
  MessageSquare, 
  FolderOpen, 
  Settings, 
  Activity,
  Cloud,
  Cpu,
  HardDrive,
  Sparkles,
  TrendingUp,
  Users,
  GitBranch
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useConfig } from '@/contexts/ConfigContext'
import { systemAPI } from '@/lib/api'
import { formatBytes, formatRelativeTime } from '@/lib/utils'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

interface SystemResources {
  cpu: { percent: number; count: number }
  memory: { percent: number; total: number; available: number }
  disk: { percent: number; total: number; free: number }
  gpu: { available: boolean; type: string }
}

export default function DivineDashboard() {
  const { discoveredServices, activeServices, isLoading, triggerDiscovery } = useConfig()
  const [systemResources, setSystemResources] = useState<SystemResources | null>(null)
  const [loadingResources, setLoadingResources] = useState(true)

  useEffect(() => {
    fetchSystemResources()
    const interval = setInterval(fetchSystemResources, 10000) // Update every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchSystemResources = async () => {
    try {
      const response = await systemAPI.getResources()
      setSystemResources(response.data)
    } catch (error) {
      console.error('Failed to fetch system resources:', error)
    } finally {
      setLoadingResources(false)
    }
  }

  const statsCards = [
    {
      title: 'Active Models',
      value: discoveredServices.ollama?.models?.length || 0,
      icon: Sparkles,
      color: 'text-olympus-gold',
      bgColor: 'bg-olympus-gold/10',
      link: '/chat'
    },
    {
      title: 'MCP Servers',
      value: discoveredServices.mcp_servers?.configured?.length || 0,
      icon: GitBranch,
      color: 'text-zeus-primary',
      bgColor: 'bg-zeus-primary/10',
      link: '/config'
    },
    {
      title: 'Active Projects',
      value: Object.keys(activeServices).filter(k => k.startsWith('project_')).length,
      icon: FolderOpen,
      color: 'text-olympus-sky',
      bgColor: 'bg-olympus-sky/10',
      link: '/projects'
    },
    {
      title: 'Webhooks',
      value: discoveredServices.webhooks?.endpoints?.length || 0,
      icon: Cloud,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      link: '/config'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Divine Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-4xl font-divine font-bold lightning-text mb-2">
          Welcome to Olympus
        </h1>
        <p className="text-gray-400">Where divine wisdom meets artificial intelligence</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Link to={stat.link}>
              <Card className="divine-card border-olympus-gold/20 hover:border-olympus-gold/40 bg-zeus-dark/50 backdrop-blur">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-400">
                    {stat.title}
                  </CardTitle>
                  <div className={`${stat.bgColor} p-2 rounded-lg`}>
                    <stat.icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* System Resources */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-divine">System Oracle</CardTitle>
                <CardDescription>Divine computational resources</CardDescription>
              </div>
              <Link to="/system">
                <Button variant="outline" size="sm" className="border-olympus-gold/20">
                  <Activity className="h-4 w-4 mr-2" />
                  View Details
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {loadingResources ? (
              <div className="space-y-4">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : systemResources ? (
              <div className="space-y-4">
                {/* CPU */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-olympus-gold" />
                      <span className="text-sm font-medium">CPU Usage</span>
                    </div>
                    <span className="text-sm text-gray-400">
                      {systemResources.cpu.percent}% ({systemResources.cpu.count} cores)
                    </span>
                  </div>
                  <Progress 
                    value={systemResources.cpu.percent} 
                    className="h-2"
                    indicatorClassName="bg-gradient-to-r from-olympus-gold to-olympus-gold-dark"
                  />
                </div>

                {/* Memory */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-zeus-primary" />
                      <span className="text-sm font-medium">Memory Usage</span>
                    </div>
                    <span className="text-sm text-gray-400">
                      {formatBytes(systemResources.memory.total - systemResources.memory.available)} / {formatBytes(systemResources.memory.total)}
                    </span>
                  </div>
                  <Progress 
                    value={systemResources.memory.percent} 
                    className="h-2"
                    indicatorClassName="bg-gradient-to-r from-zeus-primary to-zeus-primary/80"
                  />
                </div>

                {/* Disk */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-olympus-sky" />
                      <span className="text-sm font-medium">Disk Usage</span>
                    </div>
                    <span className="text-sm text-gray-400">
                      {formatBytes(systemResources.disk.free)} free
                    </span>
                  </div>
                  <Progress 
                    value={systemResources.disk.percent} 
                    className="h-2"
                    indicatorClassName="bg-gradient-to-r from-olympus-sky to-olympus-sky-dark"
                  />
                </div>

                {/* GPU Status */}
                {systemResources.gpu.available && (
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium">GPU Available</span>
                    </div>
                    <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                      {systemResources.gpu.type}
                    </Badge>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-center text-gray-400">Unable to load system resources</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-xl font-divine">Divine Actions</CardTitle>
            <CardDescription>Quick access to Olympian powers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link to="/chat">
                <Button variant="divine" className="w-full h-20 flex-col gap-2">
                  <MessageSquare className="h-6 w-6" />
                  <span>Start Divine Dialogue</span>
                </Button>
              </Link>
              <Link to="/projects">
                <Button variant="zeus" className="w-full h-20 flex-col gap-2">
                  <FolderOpen className="h-6 w-6" />
                  <span>Create Sacred Project</span>
                </Button>
              </Link>
              <Button 
                variant="outline" 
                className="w-full h-20 flex-col gap-2 border-olympus-gold/20 hover:bg-olympus-gold/10"
                onClick={() => triggerDiscovery()}
                disabled={isLoading}
              >
                <Settings className="h-6 w-6" />
                <span>Discover Services</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-divine">Divine Chronicles</CardTitle>
                <CardDescription>Recent activities in the pantheon</CardDescription>
              </div>
              <Badge variant="secondary" className="bg-olympus-gold/10 text-olympus-gold">
                <TrendingUp className="h-3 w-3 mr-1" />
                Active
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : (
                <div className="space-y-3">
                  {discoveredServices.ollama?.endpoints?.map((endpoint, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-olympus-gold/5 border border-olympus-gold/10">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-olympus-gold/10">
                          <Cloud className="h-4 w-4 text-olympus-gold" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Ollama Oracle</p>
                          <p className="text-xs text-gray-400">{endpoint}</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                        Connected
                      </Badge>
                    </div>
                  ))}
                  
                  {discoveredServices.mcp_servers?.configured?.map((server, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-zeus-primary/5 border border-zeus-primary/10">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-zeus-primary/10">
                          <GitBranch className="h-4 w-4 text-zeus-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">MCP {server.type}</p>
                          <p className="text-xs text-gray-400">{server.endpoint}</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="bg-green-500/10 text-green-500">
                        Active
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}