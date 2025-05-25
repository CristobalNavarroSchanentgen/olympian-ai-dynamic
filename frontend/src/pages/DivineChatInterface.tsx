import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Sparkles, 
  Settings, 
  Trash2, 
  RotateCcw,
  Copy,
  Download,
  Plus,
  Zap,
  Bot,
  User
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useWebSocket } from '@/contexts/WebSocketContext'
import { useConfig } from '@/contexts/ConfigContext'
import { chatAPI } from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: any
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  model: string
  created_at: string
  updated_at: string
}

export default function DivineChatInterface() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const { sendMessage, subscribe } = useWebSocket()
  const { discoveredServices } = useConfig()
  const { toast } = useToast()
  
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [message, setMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [loading, setLoading] = useState(true)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId)
    } else {
      setCurrentConversation(null)
    }
  }, [conversationId])

  useEffect(() => {
    // Subscribe to chat responses
    const unsubscribe = subscribe('chat_response', (msg) => {
      if (msg.streaming) {
        setStreamingContent(prev => prev + msg.content)
      } else if (msg.complete) {
        // Add the complete message to conversation
        if (currentConversation) {
          const assistantMessage: Message = {
            role: 'assistant',
            content: streamingContent,
            timestamp: new Date().toISOString(),
            metadata: { model: msg.model }
          }
          setCurrentConversation(prev => ({
            ...prev!,
            messages: [...prev!.messages, assistantMessage]
          }))
          setStreamingContent('')
          setIsStreaming(false)
        }
      }
    })

    return () => unsubscribe()
  }, [subscribe, currentConversation, streamingContent])

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages, streamingContent])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const response = await chatAPI.listConversations()
      setConversations(response.data.conversations)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadConversation = async (id: string) => {
    try {
      const response = await chatAPI.getConversation(id)
      setCurrentConversation(response.data)
      setSelectedModel(response.data.model)
    } catch (error) {
      console.error('Failed to load conversation:', error)
      toast({
        title: "Error",
        description: "Failed to load conversation",
        variant: "destructive"
      })
    }
  }

  const createNewConversation = async () => {
    if (!selectedModel) {
      toast({
        title: "Select a Model",
        description: "Please select a model before starting a conversation",
        variant: "destructive"
      })
      return
    }

    try {
      const response = await chatAPI.createConversation({
        model: selectedModel,
        title: `Divine Dialogue - ${new Date().toLocaleString()}`
      })
      const newConversation = response.data
      setConversations(prev => [newConversation, ...prev])
      setCurrentConversation(newConversation)
      navigate(`/chat/${newConversation.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const sendChatMessage = async () => {
    if (!message.trim() || isStreaming) return
    
    if (!currentConversation) {
      await createNewConversation()
      if (!currentConversation) return
    }

    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }

    // Add user message to conversation
    setCurrentConversation(prev => ({
      ...prev!,
      messages: [...prev!.messages, userMessage]
    }))

    // Clear input and start streaming
    setMessage('')
    setIsStreaming(true)
    setStreamingContent('')

    // Send via WebSocket for streaming
    sendMessage({
      type: 'chat',
      content: message,
      model: selectedModel,
      conversation_id: currentConversation.id
    })
  }

  const clearConversation = async () => {
    if (!currentConversation) return

    try {
      await chatAPI.clearConversation(currentConversation.id)
      setCurrentConversation(prev => ({ ...prev!, messages: [] }))
      toast({
        title: "Conversation Cleared",
        description: "The divine slate has been wiped clean"
      })
    } catch (error) {
      console.error('Failed to clear conversation:', error)
    }
  }

  const regenerateLastResponse = async () => {
    if (!currentConversation || currentConversation.messages.length < 2) return

    try {
      setIsStreaming(true)
      setStreamingContent('')
      
      // Remove last assistant message
      const messages = currentConversation.messages.slice(0, -1)
      setCurrentConversation(prev => ({ ...prev!, messages }))
      
      await chatAPI.regenerateResponse(currentConversation.id)
    } catch (error) {
      console.error('Failed to regenerate response:', error)
      setIsStreaming(false)
    }
  }

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    toast({
      title: "Copied",
      description: "Message copied to divine clipboard"
    })
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Conversation List */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-80 flex-shrink-0"
      >
        <Card className="h-full border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-divine">Divine Dialogues</CardTitle>
              <Button
                variant="divine"
                size="sm"
                onClick={() => {
                  setCurrentConversation(null)
                  navigate('/chat')
                }}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="overflow-y-auto max-h-[calc(100vh-14rem)]">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <motion.div
                    key={conv.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <button
                      onClick={() => navigate(`/chat/${conv.id}`)}
                      className={cn(
                        "w-full p-3 rounded-lg text-left transition-all",
                        conv.id === conversationId
                          ? "bg-olympus-gold/20 border border-olympus-gold/40"
                          : "bg-zeus-dark/30 hover:bg-zeus-dark/50 border border-transparent"
                      )}
                    >
                      <p className="text-sm font-medium truncate">{conv.title}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatRelativeTime(conv.updated_at)}
                      </p>
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Chat Interface */}
      <div className="flex-1 flex flex-col">
        {/* Model Selection */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4"
        >
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardContent className="py-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Label htmlFor="model-select" className="text-sm mb-2">Oracle Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger id="model-select" className="border-olympus-gold/20">
                      <SelectValue placeholder="Choose your oracle..." />
                    </SelectTrigger>
                    <SelectContent>
                      {discoveredServices.ollama?.models?.map((model) => (
                        <SelectItem key={model.name} value={model.name}>
                          <div className="flex items-center gap-2">
                            <Sparkles className="h-4 w-4 text-olympus-gold" />
                            {model.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={clearConversation}
                    disabled={!currentConversation || isStreaming}
                    className="border-olympus-gold/20"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={regenerateLastResponse}
                    disabled={!currentConversation || currentConversation.messages.length < 2 || isStreaming}
                    className="border-olympus-gold/20"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Messages */}
        <Card className="flex-1 border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur overflow-hidden">
          <CardContent className="h-full p-0">
            <div className="h-full overflow-y-auto p-6 space-y-4">
              {currentConversation?.messages.map((msg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "flex gap-4",
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-olympus-gold to-olympus-gold-dark flex items-center justify-center">
                        <Zap className="h-5 w-5 text-zeus-dark" />
                      </div>
                    </div>
                  )}
                  <div className={cn(
                    "max-w-[70%] rounded-lg p-4",
                    msg.role === 'user'
                      ? 'bg-zeus-primary/20 border border-zeus-primary/40'
                      : 'bg-olympus-gold/10 border border-olympus-gold/20'
                  )}>
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown
                        components={{
                          code({node, inline, className, children, ...props}) {
                            const match = /language-(\w+)/.exec(className || '')
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            )
                          }
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-400">
                        {formatRelativeTime(msg.timestamp)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyMessage(msg.content)}
                        className="h-6 px-2"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  {msg.role === 'user' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-zeus-primary to-zeus-primary/80 flex items-center justify-center">
                        <User className="h-5 w-5 text-white" />
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
              
              {/* Streaming Message */}
              {isStreaming && streamingContent && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-4"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-olympus-gold to-olympus-gold-dark flex items-center justify-center animate-pulse">
                      <Zap className="h-5 w-5 text-zeus-dark" />
                    </div>
                  </div>
                  <div className="max-w-[70%] rounded-lg p-4 bg-olympus-gold/10 border border-olympus-gold/20">
                    <div className="prose prose-invert max-w-none">
                      <ReactMarkdown>{streamingContent}</ReactMarkdown>
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </CardContent>
        </Card>

        {/* Input */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4"
        >
          <Card className="border-olympus-gold/20 bg-zeus-dark/50 backdrop-blur">
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      sendChatMessage()
                    }
                  }}
                  placeholder="Speak to the Oracle..."
                  className="flex-1 min-h-[60px] max-h-[200px] resize-none border-olympus-gold/20 bg-zeus-dark/30"
                  disabled={isStreaming}
                />
                <Button
                  variant="divine"
                  size="lg"
                  onClick={sendChatMessage}
                  disabled={!message.trim() || isStreaming || !selectedModel}
                  className="px-8"
                >
                  {isStreaming ? (
                    <Sparkles className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}