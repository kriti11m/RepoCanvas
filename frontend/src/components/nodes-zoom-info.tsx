"use client"

import { Card } from "@/components/ui/card"
import { Sparkles } from "lucide-react"

interface NodesZoomInfoProps {
  nodeCount: number
  zoom: number
}

export function NodesZoomInfo({ nodeCount, zoom }: NodesZoomInfoProps) {
  return (
    <div className="z-60 animate-bounce-in">
      <Card className="glass-card px-3 py-2 animate-glow-pulse">
        <div className="flex items-center gap-2 text-sm">
          <Sparkles className="w-3 h-3 text-accent animate-pulse" />
          <span className="text-gradient font-bold font-[family-name:var(--font-orbitron)] text-xs">
            NODES: {nodeCount}
          </span>
          <span className="text-muted-foreground text-xs">|</span>
          <span className="text-gradient font-bold font-[family-name:var(--font-orbitron)] text-xs">
            ZOOM: {Math.round(zoom * 100)}%
          </span>
        </div>
      </Card>
    </div>
  )
}