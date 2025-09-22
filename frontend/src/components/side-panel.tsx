"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Package, File, FenceIcon as Function, Copy, ChevronRight, Zap, Sparkles, Code, Activity, GitBranch, Search } from "lucide-react"

interface SidePanelProps {
  selectedNode: string | null
  isAnalyzing: boolean
  graphData?: { nodes: any[]; edges: any[] } | null
  onClose: () => void
}

export function SidePanel({ selectedNode, isAnalyzing, graphData, onClose }: SidePanelProps) {
  const [activeTab, setActiveTab] = useState<"summary" | "code" | "dependencies">("summary")

  // Mock data for selected node
  const nodeData = {
    react: {
      name: "React",
      type: "package",
      version: "18.2.0",
      description: "A JavaScript library for building user interfaces",
      summary: "Core React library providing component-based architecture",
      steps: ["Initialize React application", "Set up component tree", "Handle state management", "Render virtual DOM"],
      code: `import React from 'react';
import { createRoot } from 'react-dom/client';

function App() {
  const [count, setCount] = React.useState(0);
  
  return (
    <div>
      <h1>Counter: {count}</h1>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);`,
      dependencies: ["react-dom", "scheduler", "loose-envify"],
    },
    next: {
      name: "Next.js",
      type: "package",
      version: "13.4.0",
      description: "The React Framework for Production",
      summary: "Full-stack React framework with server-side rendering",
      steps: ["Set up Next.js app", "Configure routing", "Add API routes", "Deploy to production"],
      code: `import type { NextPage } from 'next';
import Head from 'next/head';

const Home: NextPage = () => {
  return (
    <div>
      <Head>
        <title>My Next.js App</title>
      </Head>
      <main>
        <h1>Welcome to Next.js!</h1>
      </main>
    </div>
  );
};

export default Home;`,
      dependencies: ["react", "react-dom", "@next/swc-linux-x64-gnu"],
    },
  }

  const currentNode = selectedNode ? nodeData[selectedNode as keyof typeof nodeData] : null

  if (isAnalyzing) {
    return (
      <Card className="h-full glass-card border-0 shadow-2xl animate-slide-in-right animate-glow-pulse">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
              ⚡ ANALYZING
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={onClose} className="lg:hidden glass-button">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[calc(100%-100px)]">
          <div className="text-center space-y-6">
            <div className="relative">
              <Activity className="w-16 h-16 mx-auto animate-spin text-accent" />
            </div>
            <p className="text-gradient font-bold text-lg font-[family-name:var(--font-orbitron)]">
              ANALYZING REPOSITORY...
            </p>
            <div className="text-sm opacity-70 text-gray-400">
              Parsing code structure and dependencies
            </div>
            <div className="flex justify-center gap-1">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="w-2 h-2 bg-primary rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Show analysis complete or ready state when no node is selected
  if (!selectedNode || !currentNode) {
    return (
      <Card className="h-full glass-card border-0 shadow-2xl">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
              🎯 ANALYSIS
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={onClose} className="lg:hidden glass-button">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[calc(100%-100px)]">
          {!selectedNode ? (
            <div className="text-center space-y-4">
              {graphData ? (
                <>
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-accent/20 to-primary/20 rounded-2xl flex items-center justify-center">
                    <GitBranch className="w-8 h-8 text-accent" />
                  </div>
                  <div className="text-lg font-semibold text-gradient">Repository Analysis Complete</div>
                  <div className="text-sm opacity-70 text-gray-400 mt-2">
                    {graphData.nodes?.length || 0} nodes, {graphData.edges?.length || 0} edges processed
                  </div>
                  <div className="text-xs opacity-50 mt-4 text-gray-500">
                    Click on any node in the graph to explore dependencies
                  </div>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl flex items-center justify-center">
                    <Search className="w-8 h-8 text-primary" />
                  </div>
                  <div className="text-lg font-semibold text-gradient">Ready to Analyze</div>
                  <div className="text-sm opacity-70 text-gray-400 mt-2">
                    Enter a repository URL and click ANALYZE to get started
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="text-center space-y-6">
              <div className="relative">
                <Package className="w-16 h-16 text-primary mx-auto animate-float" />
                <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-accent animate-pulse" />
              </div>
              <p className="text-gradient font-bold text-base font-[family-name:var(--font-orbitron)]">SELECT A NODE</p>
              <p className="text-muted-foreground text-xs">Click on any dependency to explore</p>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full glass-card border-2 border-primary/30 shadow-2xl animate-slide-in-right animate-glow-pulse shadow-primary/20 glow-border z-40 relative">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-primary to-accent rounded-xl">
              {currentNode.type === "package" && <Package className="w-5 h-5 text-white" />}
              {currentNode.type === "file" && <File className="w-5 h-5 text-white" />}
              {currentNode.type === "function" && <Function className="w-5 h-5 text-white" />}
            </div>
            <CardTitle className="text-lg font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
              {currentNode.name.toUpperCase()}
            </CardTitle>
            <Sparkles className="w-5 h-5 text-accent animate-pulse" />
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="lg:hidden glass-button">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex gap-2 mt-2">
          <Badge
            variant="secondary"
            className="glass-card border-accent/30 text-accent font-bold px-2 py-1 text-xs minecraft-border"
          >
            ⚡ {currentNode.type.toUpperCase()}
          </Badge>
          {currentNode.version && (
            <Badge variant="outline" className="glass-card border-primary/30 text-primary font-bold px-2 py-1 text-xs minecraft-border">
              🚀 v{currentNode.version}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0 overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-muted/20 bg-muted/5 overflow-hidden">
          <button
            onClick={() => setActiveTab("summary")}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors minecraft-border ${
              activeTab === "summary"
                ? "bg-primary/20 text-primary border-b-2 border-primary glow-text"
                : "hover:bg-muted/10 text-muted-foreground"
            }`}
          >
            Summary
          </button>
          <button
            onClick={() => setActiveTab("code")}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors minecraft-border ${
              activeTab === "code"
                ? "bg-primary/20 text-primary border-b-2 border-primary glow-text"
                : "hover:bg-muted/10 text-muted-foreground"
            }`}
          >
            Code
          </button>
          <button
            onClick={() => setActiveTab("dependencies")}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors minecraft-border ${
              activeTab === "dependencies"
                ? "bg-primary/20 text-primary border-b-2 border-primary glow-text"
                : "hover:bg-muted/10 text-muted-foreground"
            }`}
          >
            Dependencies
          </button>
        </div>

        <ScrollArea className="h-[calc(100vh-280px)] p-4">
          {activeTab === "summary" && (
            <div className="space-y-4">
              <div className="glass-card p-4 minecraft-border">
                <h4 className="font-semibold text-sm mb-2 text-gradient minecraft-text">Description</h4>
                <p className="text-xs text-foreground leading-relaxed">{currentNode.summary}</p>
              </div>

              <div className="glass-card p-4 minecraft-border">
                <h4 className="font-semibold text-sm mb-3 text-gradient minecraft-text">
                  Implementation Steps ({currentNode.steps.length})
                </h4>
                <div className="space-y-2">
                  {currentNode.steps.map((step, index) => (
                    <div key={index} className="flex gap-3">
                      <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5 minecraft-border">
                        <span className="text-xs font-bold text-primary">{index + 1}</span>
                      </div>
                      <p className="text-xs text-foreground leading-relaxed">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "code" && (
            <div className="space-y-4">
              <div className="glass-card minecraft-border overflow-hidden">
                <div className="flex items-center justify-between p-3 border-b border-muted/20 bg-muted/5">
                  <h4 className="font-semibold text-sm text-gradient minecraft-text">Source Code</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs px-2 py-1 h-auto glass-button minecraft-border"
                    onClick={() => navigator.clipboard.writeText(currentNode.code)}
                  >
                    <Copy className="w-3 h-3 mr-1" />
                    Copy
                  </Button>
                </div>
                <div className="p-3 bg-muted/2 font-mono text-xs overflow-x-auto">
                  <pre className="text-foreground whitespace-pre-wrap leading-relaxed">{currentNode.code}</pre>
                </div>
              </div>
            </div>
          )}

          {activeTab === "dependencies" && (
            <div className="space-y-3">
              <h4 className="font-semibold text-sm text-gradient minecraft-text">
                Dependencies ({currentNode.dependencies.length})
              </h4>
              <div className="space-y-2">
                {currentNode.dependencies.map((dep, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-2 glass-card hover:bg-primary/10 transition-colors cursor-pointer minecraft-border"
                  >
                    <Package className="w-4 h-4 text-accent flex-shrink-0" />
                    <span className="text-sm font-medium text-foreground">{dep}</span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground ml-auto" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}