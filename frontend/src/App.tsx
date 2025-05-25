import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/Layout'
import DivineDashboard from '@/pages/DivineDashboard'
import DivineChatInterface from '@/pages/DivineChatInterface'
import ProjectWorkspace from '@/pages/ProjectWorkspace'
import DynamicConfiguration from '@/pages/DynamicConfiguration'
import SystemMonitoring from '@/pages/SystemMonitoring'
import { ThemeProvider } from '@/components/theme-provider'
import { WebSocketProvider } from '@/contexts/WebSocketContext'
import { ConfigProvider } from '@/contexts/ConfigContext'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="olympian-theme">
      <ConfigProvider>
        <WebSocketProvider>
          <Layout>
            <Routes>
              <Route path="/" element={<DivineDashboard />} />
              <Route path="/chat" element={<DivineChatInterface />} />
              <Route path="/chat/:conversationId" element={<DivineChatInterface />} />
              <Route path="/projects" element={<ProjectWorkspace />} />
              <Route path="/projects/:projectId" element={<ProjectWorkspace />} />
              <Route path="/config" element={<DynamicConfiguration />} />
              <Route path="/system" element={<SystemMonitoring />} />
            </Routes>
          </Layout>
          <Toaster />
        </WebSocketProvider>
      </ConfigProvider>
    </ThemeProvider>
  )
}

export default App