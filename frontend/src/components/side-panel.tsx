"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Package, File, FenceIcon as Function, Copy, ChevronRight, Zap, Sparkles, Code } from "lucide-react"

interface SidePanelProps {
  selectedNode: string | null
  isAnalyzing: boolean
  onClose: () => void
}

export function SidePanel({ selectedNode, isAnalyzing, onClose }: SidePanelProps) {
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
      version: "14.0.0",
      description: "The React Framework for Production",
      summary: "Full-stack React framework with SSR and routing",
      steps: [
        "Configure Next.js application",
        "Set up file-based routing",
        "Enable server-side rendering",
        "Optimize for production",
      ],
      code: `// app/page.tsx
export default function HomePage() {
  return (
    <main>
      <h1>Welcome to Next.js!</h1>
      <p>This is a server-rendered page.</p>
    </main>
  );
}

// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
};

module.exports = nextConfig;`,
      dependencies: ["react", "react-dom", "@next/swc-win32-x64-msvc"],
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
              <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <Sparkles className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 text-accent animate-pulse" />
            </div>
            <p className="text-gradient font-bold text-lg font-[family-name:var(--font-orbitron)]">
              SCANNING REPOSITORY...
            </p>
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
          <div className="text-center space-y-6">
            <div className="relative">
              <Package className="w-16 h-16 text-primary mx-auto animate-float" />
              <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-accent animate-pulse" />
            </div>
            <p className="text-gradient font-bold text-base font-[family-name:var(--font-orbitron)]">SELECT A NODE</p>
            <p className="text-muted-foreground text-xs">Click on any dependency to explore</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full glass-card border-0 shadow-2xl animate-slide-in-right animate-glow-pulse shadow-primary/10 glow-border">
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
        <div className="flex items-center gap-3">
          <Badge className="glass-card border-accent/30 text-accent font-bold px-2 py-1 text-xs">
            ⚡ {currentNode.type.toUpperCase()}
          </Badge>
          {currentNode.version && (
            <Badge className="glass-card border-primary/30 text-primary font-bold px-2 py-1 text-xs">
              🚀 v{currentNode.version}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6 h-[calc(100%-140px)]">
        {/* Tab Navigation */}
        <div className="flex gap-1 p-2 glass-card rounded-xl justify-center">
          {(
            [
              ["summary", "📊"],
              ["code", "💻"],
              ["dependencies", "🔗"],
            ] as const
          ).map(([tab, icon]) => (
            <Button
              key={tab}
              variant={activeTab === tab ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 text-xs font-bold font-[family-name:var(--font-orbitron)] tracking-wide ${
                activeTab === tab ? "glass-button" : "hover:bg-primary/10"
              }`}
            >
              {icon} {tab.toUpperCase()}
            </Button>
          ))}
        </div>

        <ScrollArea className="h-full">
          {activeTab === "summary" && (
            <div className="space-y-6">
              <div className="glass-card p-4 rounded-2xl">
                <h3 className="font-bold text-base mb-3 text-gradient font-[family-name:var(--font-orbitron)] flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  OVERVIEW
                </h3>
                <p className="text-xs text-foreground leading-relaxed">{currentNode.summary}</p>
              </div>

              <div className="glass-card p-4 rounded-2xl">
                <h3 className="font-bold text-base mb-4 text-gradient font-[family-name:var(--font-orbitron)] flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  EXECUTION STEPS
                </h3>
                <ol className="space-y-2">
                  {currentNode.steps.map((step, index) => (
                    <li key={index} className="flex items-start gap-3 text-xs">
                      <span className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-primary to-accent text-white rounded-lg flex items-center justify-center text-xs font-bold font-[family-name:var(--font-orbitron)] shadow-lg">
                        {index + 1}
                      </span>
                      <span className="text-foreground leading-relaxed pt-1">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}

          {activeTab === "code" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-base text-gradient font-[family-name:var(--font-orbitron)] flex items-center gap-2">
                  💻 CODE SAMPLE
                </h3>
                <Button className="glass-button h-7 px-2 text-xs font-bold">
                  <Copy className="w-3 h-3 mr-1" />
                  COPY
                </Button>
              </div>
              <div className="glass-card p-4 rounded-2xl font-mono text-xs overflow-x-auto">
                <pre className="text-foreground whitespace-pre-wrap leading-relaxed">{currentNode.code}</pre>
              </div>
            </div>
          )}

          {activeTab === "dependencies" && (
            <div className="space-y-4">
              <h3 className="font-bold text-base text-gradient font-[family-name:var(--font-orbitron)] flex items-center gap-2">
                🔗 DEPENDENCIES
              </h3>
              <div className="space-y-2">
                {currentNode.dependencies.map((dep, index) => (
                  <div
                    key={index}
                    className="glass-card p-2 rounded-xl hover:bg-primary/5 transition-all duration-300"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-primary to-accent rounded-md flex items-center justify-center">
                          <Package className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-xs font-mono font-bold">{dep}</span>
                      </div>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0 hover:bg-accent/20">
                        <ChevronRight className="w-3 h-3 text-accent" />
                      </Button>
                    </div>
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
