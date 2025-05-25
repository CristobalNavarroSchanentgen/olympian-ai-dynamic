import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Plus,
  Save,
  Upload,
  Download,
  Trash2,
  Copy,
  Settings,
  FileText,
  Code,
  Image,
  Music,
  Video,
  FolderOpen,
  X,
  Archive,
  Edit
} from 'lucide-react'
import { projectAPI } from '@/lib/api'
import { useConfig } from '@/contexts/ConfigContext'
import { cn, formatBytes, formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'

interface Project {
  id: string
  name: string
  description?: string
  model: string
  system_prompt?: string
  temperature: number
  tools: string[]
  context_files: string[]
  created_at: string
  updated_at: string
  active: boolean
  statistics: {
    total_messages: number
    total_tokens: number
    last_used?: string
  }
}

export default function ProjectWorkspace() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const { discoveredServices } = useConfig()
  const { toast } = useToast()
  
  const [projects, setProjects] = useState<Project[]>([])
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  
  // Form states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    model: '',
    system_prompt: '',
    temperature: 0.7,
    tools: [] as string[]
  })
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editMode, setEditMode] = useState(false)

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (projectId) {
      loadProject(projectId)
    } else {
      setCurrentProject(null)
      setEditMode(false)
    }
  }, [projectId])

  const loadProjects = async () => {
    try {
      const response = await projectAPI.list()
      setProjects(response.data.projects)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadProject = async (id: string) => {
    try {
      const response = await projectAPI.get(id)
      setCurrentProject(response.data)
      setFormData({
        name: response.data.name,
        description: response.data.description || '',
        model: response.data.model,
        system_prompt: response.data.system_prompt || '',
        temperature: response.data.temperature,
        tools: response.data.tools || []
      })
    } catch (error) {
      console.error('Failed to load project:', error)
      toast({
        title: "Error",
        description: "Failed to load project",
        variant: "destructive"
      })
    }
  }

  const createProject = async () => {
    try {
      setSaving(true)
      const response = await projectAPI.create(formData)
      const newProject = response.data
      setProjects(prev => [newProject, ...prev])
      setCreateDialogOpen(false)
      navigate(`/projects/${newProject.id}`)
      toast({
        title: "Project Created",
        description: "Your sacred workspace has been established"
      })
    } catch (error) {
      console.error('Failed to create project:', error)
      toast({
        title: "Error",
        description: "Failed to create project",
        variant: "destructive"
      })
    } finally {
      setSaving(false)
    }
  }

  const updateProject = async () => {
    if (!currentProject) return
    
    try {
      setSaving(true)
      const response = await projectAPI.update(currentProject.id, formData)
      setCurrentProject(response.data)
      setEditMode(false)
      toast({
        title: "Project Updated",
        description: "Your sacred workspace has been updated"
      })
    } catch (error) {
      console.error('Failed to update project:', error)
      toast({
        title: "Error",
        description: "Failed to update project",
        variant: "destructive"
      })
    } finally {
      setSaving(false)
    }
  }

  const deleteProject = async (id: string) => {
    try {
      await projectAPI.delete(id)
      setProjects(prev => prev.filter(p => p.id !== id))
      if (currentProject?.id === id) {
        navigate('/projects')
      }
      toast({
        title: "Project Deleted",
        description: "The sacred workspace has been removed"
      })
    } catch (error) {
      console.error('Failed to delete project:', error)
      toast({
        title: "Error",
        description: "Failed to delete project",
        variant: "destructive"
      })
    }
  }

  const duplicateProject = async (id: string) => {
    try {
      const response = await projectAPI.duplicate(id)
      const duplicated = response.data
      setProjects(prev => [duplicated, ...prev])
      toast({
        title: "Project Duplicated",
        description: "A divine copy has been created"
      })
    } catch (error) {
      console.error('Failed to duplicate project:', error)
    }
  }

  const getGenerationIcon = (type: string) => {
    switch (type) {
      case 'code': return Code
      case 'document': return FileText
      case 'image': return Image
      case 'audio': return Music
      case 'video': return Video
      default: return FileText
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Project List */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-80 flex-shrink-0"
      >
        <Card className="h-full border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-divine">Sacred Projects</CardTitle>
              <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="divine" size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[525px] bg-zeus-dark/95 backdrop-blur border-olympus-gold/20">
                  <DialogHeader>
                    <DialogTitle className="font-divine">Create Sacred Project</DialogTitle>
                    <DialogDescription>
                      Establish a new divine workspace for your AI endeavors
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label htmlFor="name">Project Name</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Divine Creation"
                        className="border-olympus-gold/20"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe your divine purpose..."
                        className="border-olympus-gold/20"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="model">Oracle Model</Label>
                      <Select 
                        value={formData.model} 
                        onValueChange={(value) => setFormData(prev => ({ ...prev, model: value }))}
                      >
                        <SelectTrigger className="border-olympus-gold/20">
                          <SelectValue placeholder="Choose your oracle..." />
                        </SelectTrigger>
                        <SelectContent>
                          {discoveredServices.ollama?.models?.map((model) => (
                            <SelectItem key={model.name} value={model.name}>
                              {model.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button 
                      variant="divine" 
                      onClick={createProject}
                      disabled={!formData.name || !formData.model || saving}
                    >
                      {saving ? 'Creating...' : 'Create Project'}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent className="overflow-y-auto max-h-[calc(100vh-14rem)]">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            ) : (
              <div className="space-y-2">
                {projects.map((project) => (
                  <motion.div
                    key={project.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <button
                      onClick={() => navigate(`/projects/${project.id}`)}
                      className={cn(
                        "w-full p-3 rounded-lg text-left transition-all",
                        project.id === projectId
                          ? "bg-olympus-gold/20 border border-olympus-gold/40"
                          : "bg-zeus-dark/30 hover:bg-zeus-dark/50 border border-transparent"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium">{project.name}</p>
                          {project.description && (
                            <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                              {project.description}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="text-xs">
                              {project.model}
                            </Badge>
                            {!project.active && (
                              <Badge variant="secondary" className="text-xs bg-gray-600/20">
                                <Archive className="h-3 w-3 mr-1" />
                                Archived
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Project Details */}
      {currentProject ? (
        <div className="flex-1 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {/* Project Header */}
            <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {editMode ? (
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="text-2xl font-divine border-olympus-gold/20 mb-2"
                      />
                    ) : (
                      <CardTitle className="text-2xl font-divine">{currentProject.name}</CardTitle>
                    )}
                    {editMode ? (
                      <Textarea
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        className="border-olympus-gold/20 mt-2"
                        placeholder="Project description..."
                      />
                    ) : (
                      currentProject.description && (
                        <CardDescription className="mt-2">{currentProject.description}</CardDescription>
                      )
                    )}
                  </div>
                  <div className="flex gap-2">
                    {editMode ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditMode(false)
                            loadProject(currentProject.id)
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          variant="divine"
                          size="sm"
                          onClick={updateProject}
                          disabled={saving}
                        >
                          <Save className="h-4 w-4 mr-2" />
                          Save
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditMode(true)}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => duplicateProject(currentProject.id)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteProject(currentProject.id)}
                          className="text-red-500 hover:text-red-400"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
                  <span>Created {formatRelativeTime(currentProject.created_at)}</span>
                  <span>•</span>
                  <span>Updated {formatRelativeTime(currentProject.updated_at)}</span>
                  {currentProject.statistics.last_used && (
                    <>
                      <span>•</span>
                      <span>Last used {formatRelativeTime(currentProject.statistics.last_used)}</span>
                    </>
                  )}
                </div>
              </CardHeader>
            </Card>

            {/* Project Tabs */}
            <Tabs defaultValue="configuration" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4 bg-zeus-dark/50">
                <TabsTrigger value="configuration">Configuration</TabsTrigger>
                <TabsTrigger value="context">Context</TabsTrigger>
                <TabsTrigger value="tools">Tools</TabsTrigger>
                <TabsTrigger value="statistics">Statistics</TabsTrigger>
              </TabsList>

              {/* Configuration Tab */}
              <TabsContent value="configuration">
                <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
                  <CardHeader>
                    <CardTitle>Project Configuration</CardTitle>
                    <CardDescription>Divine parameters for your workspace</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid gap-4">
                      <div className="grid gap-2">
                        <Label>Oracle Model</Label>
                        <Select 
                          value={formData.model} 
                          onValueChange={(value) => setFormData(prev => ({ ...prev, model: value }))}
                          disabled={!editMode}
                        >
                          <SelectTrigger className="border-olympus-gold/20">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {discoveredServices.ollama?.models?.map((model) => (
                              <SelectItem key={model.name} value={model.name}>
                                {model.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="grid gap-2">
                        <Label>System Prompt</Label>
                        <Textarea
                          value={formData.system_prompt}
                          onChange={(e) => setFormData(prev => ({ ...prev, system_prompt: e.target.value }))}
                          placeholder="Divine instructions for the AI oracle..."
                          className="min-h-[100px] border-olympus-gold/20"
                          disabled={!editMode}
                        />
                      </div>

                      <div className="grid gap-2">
                        <div className="flex items-center justify-between">
                          <Label>Temperature</Label>
                          <span className="text-sm text-gray-400">{formData.temperature}</span>
                        </div>
                        <Slider
                          value={[formData.temperature]}
                          onValueChange={([value]) => setFormData(prev => ({ ...prev, temperature: value }))}
                          min={0}
                          max={2}
                          step={0.1}
                          disabled={!editMode}
                          className="py-4"
                        />
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Focused</span>
                          <span>Creative</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Context Tab */}
              <TabsContent value="context">
                <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
                  <CardHeader>
                    <CardTitle>Context Files</CardTitle>
                    <CardDescription>Sacred texts and knowledge for your project</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-center py-8 border-2 border-dashed border-olympus-gold/20 rounded-lg">
                      <div className="text-center">
                        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-sm text-gray-400 mb-2">Drop files here or click to upload</p>
                        <Button variant="outline" size="sm">
                          <Upload className="h-4 w-4 mr-2" />
                          Select Files
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Tools Tab */}
              <TabsContent value="tools">
                <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
                  <CardHeader>
                    <CardTitle>Divine Tools</CardTitle>
                    <CardDescription>MCP tools available for this project</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {discoveredServices.mcp_servers?.configured?.map((server) => (
                        <div key={server.id} className="space-y-2">
                          <h4 className="text-sm font-medium">{server.type} Server</h4>
                          <div className="grid grid-cols-2 gap-2">
                            {server.tools?.map((tool: any) => (
                              <div key={tool} className="flex items-center gap-2">
                                <Switch
                                  checked={formData.tools.includes(tool)}
                                  onCheckedChange={(checked) => {
                                    if (checked) {
                                      setFormData(prev => ({ 
                                        ...prev, 
                                        tools: [...prev.tools, tool] 
                                      }))
                                    } else {
                                      setFormData(prev => ({ 
                                        ...prev, 
                                        tools: prev.tools.filter(t => t !== tool) 
                                      }))
                                    }
                                  }}
                                  disabled={!editMode}
                                />
                                <Label className="text-sm">{tool}</Label>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Statistics Tab */}
              <TabsContent value="statistics">
                <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
                  <CardHeader>
                    <CardTitle>Project Statistics</CardTitle>
                    <CardDescription>Divine metrics and usage data</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-sm text-gray-400">Total Messages</p>
                        <p className="text-2xl font-bold">{currentProject.statistics.total_messages}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-gray-400">Total Tokens</p>
                        <p className="text-2xl font-bold">{currentProject.statistics.total_tokens.toLocaleString()}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </motion.div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <FolderOpen className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-divine text-gray-400 mb-2">No Project Selected</h3>
            <p className="text-gray-500 mb-4">Select a project from the list or create a new one</p>
            <Button variant="divine" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Sacred Project
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}