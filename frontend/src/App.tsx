import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, GitBranch, Activity, Bot, Zap, Sparkles } from "lucide-react"
import RepoForceGraph from "@/components/repo-force-graph"
import { SidePanel } from "@/components/side-panel"
import { ControlsBar } from "@/components/controls-bar"
import { CyberBackground } from "@/components/cyber-background"
import { AIChatbot } from "@/components/ai-chatbot"
import { TestThree } from "@/components/test-three" // Testing three.js
// import { useCursorTrail } from "@/hooks/use-cursor-trail" - DISABLED
import { NodesZoomInfo } from "@/components/nodes-zoom-info"
import { apiService, type GraphData } from "@/services/api"
import { useToast } from "@/hooks/use-toast"
import { Toaster } from "@/components/ui/toaster"

function App() {
  const [repoUrl, setRepoUrl] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState([1])
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [showSidePanel, setShowSidePanel] = useState(true)
  const [showAIChat, setShowAIChat] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [nodeCount, setNodeCount] = useState(0)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [analysisJobId, setAnalysisJobId] = useState<string | null>(null)
  const [searchServiceStatus, setSearchServiceStatus] = useState<"unknown" | "working" | "error">("unknown")
  const { toast } = useToast()

  // Add cursor trail effect - DISABLED
  // useCursorTrail()

  // Extract repository name from URL
  const getRepoName = (url: string) => {
    try {
      const urlParts = url.trim().replace(/\/$/, '').split('/')
      return urlParts[urlParts.length - 1] || 'Repository'
    } catch {
      return 'Repository'
    }
  }

  useEffect(() => {
    console.log("App.tsx component mounted")
    console.log("CyberBackground imported:", CyberBackground)
  }, [])

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) {
      toast({
        title: "Repository URL Required",
        description: "Please enter a valid repository URL",
        variant: "destructive"
      })
      return
    }

    setIsAnalyzing(true)
    setShowSidePanel(true)
    setAnalysisJobId(null)

    try {
      toast({
        title: "Starting Analysis",
        description: "Parsing and indexing your repository...",
      })

      const response = await apiService.analyzeRepository({
        repo_url: repoUrl,
        branch: "main"
      })

      if (response.success && response.job_id) {
        setAnalysisJobId(response.job_id)
        
        // Poll job status
        const pollJob = async () => {
          try {
            const status = await apiService.getJobStatus(response.job_id!)
            
            if (status.status === 'completed') {
              setIsAnalyzing(false)
              toast({
                title: "Analysis Complete",
                description: "Repository has been successfully analyzed!",
              })
              
              // Load graph data
              await loadGraphData()
            } else if (status.status === 'failed') {
              setIsAnalyzing(false)
              toast({
                title: "Analysis Failed",
                description: status.error || "Failed to analyze repository",
                variant: "destructive"
              })
            } else if (status.status === 'running' || status.status === 'pending') {
              // Continue polling
              setTimeout(pollJob, 2000)
            }
          } catch (error) {
            console.error('Job polling error:', error)
            setTimeout(pollJob, 5000) // Retry with longer interval
          }
        }
        
        setTimeout(pollJob, 2000)
      } else {
        setIsAnalyzing(false)
        toast({
          title: "Analysis Failed",
          description: response.error || "Failed to start analysis",
          variant: "destructive"
        })
      }
    } catch (error: any) {
      setIsAnalyzing(false)
      toast({
        title: "Analysis Failed",
        description: error.message,
        variant: "destructive"
      })
    }
  }

  const loadGraphData = async () => {
    try {
      const data = await apiService.getGraphData()
      setGraphData(data)
      setSearchServiceStatus("working")
    } catch (error) {
      console.error('Failed to load graph data:', error)
      setSearchServiceStatus("error")
    }
  }

  const handleChatbotResponse = (success: boolean) => {
    if (success) {
      setSearchServiceStatus("working")
    } else {
      setSearchServiceStatus("error")
    }
  }

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNode(nodeId)
    setShowSidePanel(true)
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ backgroundColor: 'transparent' }}>
      <CyberBackground />

      <header className="border-0 sticky top-0 z-50" style={{ 
        background: 'transparent', 
        backdropFilter: 'none'
      }}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-2xl flex items-center justify-center shadow-lg animate-pulse-node minecraft-border animate-glow-pulse">
                <GitBranch className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-black text-gradient font-[family-name:var(--font-orbitron)] tracking-wider minecraft-text animate-glow-pulse">
                REPOCANVAS
              </h1>
              <Sparkles className="w-5 h-5 text-accent animate-pulse" />
            </div>

            <div className="flex-1 flex items-center gap-4 max-w-5xl">
              <div className="flex-1 relative group">
                <Input
                  placeholder="🚀 Enter repository URL (e.g., https://github.com/user/repo)"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="glass-card border-primary/30 font-mono h-12 text-lg placeholder:text-muted-foreground/70 focus:border-accent focus:ring-accent/50 transition-all duration-300 minecraft-border"
                />
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!repoUrl.trim() || isAnalyzing}
                className="glass-button h-12 px-8 text-lg font-bold font-[family-name:var(--font-orbitron)] tracking-wide shadow-lg minecraft-border animate-glow-pulse"
              >
                {isAnalyzing ? (
                  <>
                    <Activity className="w-5 h-5 mr-3 animate-spin" />
                    ANALYZING...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 mr-3" />
                    ANALYZE
                  </>
                )}
              </Button>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowAIChat(!showAIChat)}
              className="glass-card w-12 h-12 hover:bg-primary/20 transition-all duration-300 minecraft-border animate-glow-pulse"
            >
              <Bot className="w-5 h-5 text-accent" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 relative z-10 max-w-full">
        <div className="grid grid-cols-1 lg:grid-cols-6 gap-6 h-[calc(100vh-180px)]">
          <div className={`${showSidePanel ? "lg:col-span-4" : "lg:col-span-6"} transition-all duration-500`}>
            <Card className="h-full invisible-glass border-0 shadow-none">
              <CardHeader className="pb-2 bg-transparent">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
                    DEPENDENCY GRAPH
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className="glass-card border-accent/30 text-accent font-bold px-2 py-1 text-xs"
                    >
                      {selectedNode ? `🎯 ${selectedNode}` : "🔍 No selection"}
                    </Badge>
                    {searchServiceStatus === "error" && (
                      <Badge
                        variant="destructive"
                        className="glass-card border-red-500/30 text-red-400 font-bold px-2 py-1 text-xs"
                      >
                        ⚠️ Search Offline
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowSidePanel(!showSidePanel)}
                      className="lg:hidden glass-button text-xs px-2"
                    >
                      {showSidePanel ? "Hide Panel" : "Show Panel"}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0 h-[calc(100%-80px)] bg-transparent">
                <div className="flex h-full">
                  {/* Repository Graph - Now takes full width when no side panel */}
                  <div className={`${showSidePanel ? "w-full" : "w-full"} h-full bg-transparent overflow-hidden`}>
                    <div className="h-full relative max-w-full max-h-full overflow-hidden">
                      <RepoForceGraph
                        graphData={graphData ?? undefined}
                        repoName={repoUrl ? getRepoName(repoUrl) : undefined}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {showSidePanel && (
            <div className="lg:col-span-2 animate-slide-in-right">
              <SidePanel
                selectedNode={selectedNode}
                isAnalyzing={isAnalyzing}
                graphData={graphData}
                onClose={() => setShowSidePanel(false)}
              />
            </div>
          )}
        </div>
      </main>

      {/* Centered control components below dependency graph */}
      <div className="fixed bottom-16 left-[45%] transform -translate-x-1/2 flex items-center gap-6 z-60">
        <div>
          <ControlsBar
            isPlaying={isPlaying}
            onPlayPause={() => setIsPlaying(!isPlaying)}
            speed={speed}
            onSpeedChange={setSpeed}
            isDemoMode={isDemoMode}
            onDemoModeChange={setIsDemoMode}
          />
        </div>
        <div>
          <NodesZoomInfo nodeCount={nodeCount} zoom={zoom} />
        </div>
      </div>

      {showAIChat && (
        <AIChatbot 
          onClose={() => setShowAIChat(false)} 
          onGraphUpdate={setGraphData}
          onResponseStatus={handleChatbotResponse}
          currentGraphData={graphData}
        />
      )}
      
      <Toaster />
    </div>
  )
}

export default App