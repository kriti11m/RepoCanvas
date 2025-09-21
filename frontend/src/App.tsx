import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, GitBranch, Activity, Bot, Zap, Sparkles } from "lucide-react"
import { GraphCanvas } from "@/components/graph-canvas"
import { SidePanel } from "@/components/side-panel"
import { ControlsBar } from "@/components/controls-bar"
import { CyberBackground } from "@/components/cyber-background"
import { AIChatbot } from "@/components/ai-chatbot"
import { TestThree } from "@/components/test-three" // Testing three.js

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

  useEffect(() => {
    console.log("App.tsx component mounted")
    console.log("CyberBackground imported:", CyberBackground)
  }, [])

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) return

    setIsAnalyzing(true)
    setShowSidePanel(true)

    // Simulate analysis delay
    await new Promise((resolve) => setTimeout(resolve, 2000))
    setIsAnalyzing(false)
  }

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNode(nodeId)
    setShowSidePanel(true)
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ backgroundColor: 'transparent' }}>
      <CyberBackground />

      <header className="border-0 sticky top-0 z-50 animate-glow-pulse" style={{ 
        background: 'rgba(0, 50, 100, 0.15)', 
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(0, 153, 255, 0.25)' 
      }}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-accent rounded-2xl flex items-center justify-center shadow-lg animate-pulse-node minecraft-border">
                <GitBranch className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-black text-gradient font-[family-name:var(--font-orbitron)] tracking-wider minecraft-text">
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
                  className="glass-card border-primary/30 font-mono text-sm h-12 text-lg placeholder:text-muted-foreground/70 focus:border-accent focus:ring-accent/50 transition-all duration-300 minecraft-border"
                />
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>

              <div className="relative group">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-accent z-10" />
                <Input
                  placeholder="🔍 Search dependencies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="glass-card border-primary/30 pl-12 w-72 h-12 text-lg focus:border-accent focus:ring-accent/50 transition-all duration-300 minecraft-border"
                />
              </div>

              <Button
                onClick={handleAnalyze}
                disabled={!repoUrl.trim() || isAnalyzing}
                className="glass-button h-12 px-8 text-lg font-bold font-[family-name:var(--font-orbitron)] tracking-wide shadow-lg minecraft-border"
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
              className="glass-card w-12 h-12 hover:bg-primary/20 transition-all duration-300 minecraft-border"
            >
              <Bot className="w-5 h-5 text-accent" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-12 py-8 relative z-10 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-6 gap-6 h-[calc(100vh-180px)] mx-auto justify-center ml-8">
          <div className={`${showSidePanel ? "lg:col-span-4" : "lg:col-span-6"} transition-all duration-500`}>
            <Card className="h-full invisible-glass border-0 shadow-none">
              <CardHeader className="pb-4 bg-transparent">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-2xl font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
                    DEPENDENCY GRAPH
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="secondary"
                      className="glass-card border-accent/30 text-accent font-bold px-3 py-1 text-xs"
                    >
                      {selectedNode ? `🎯 ${selectedNode}` : "🔍 No selection"}
                    </Badge>
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
              <CardContent className="p-0 h-[calc(100%-100px)] bg-transparent">
                <GraphCanvas
                  onNodeSelect={handleNodeSelect}
                  selectedNode={selectedNode}
                  isPlaying={isPlaying}
                  speed={speed[0]}
                  searchQuery={searchQuery}
                />
              </CardContent>
            </Card>
          </div>

          {showSidePanel && (
            <div className="lg:col-span-2 animate-slide-in-right">
              <SidePanel
                selectedNode={selectedNode}
                isAnalyzing={isAnalyzing}
                onClose={() => setShowSidePanel(false)}
              />
            </div>
          )}
        </div>
      </main>

      <ControlsBar
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying(!isPlaying)}
        speed={speed}
        onSpeedChange={setSpeed}
        isDemoMode={isDemoMode}
        onDemoModeChange={setIsDemoMode}
      />

      {showAIChat && <AIChatbot onClose={() => setShowAIChat(false)} />}
    </div>
  )
}

export default App