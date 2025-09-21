"use client"

import type React from "react"

import { useEffect, useRef, useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut, RotateCcw, Sparkles } from "lucide-react"

interface Node {
  id: string
  label: string
  type: "package" | "file" | "function"
  x: number
  y: number
  dependencies: string[]
}

interface GraphCanvasProps {
  onNodeSelect: (nodeId: string) => void
  selectedNode: string | null
  isPlaying: boolean
  speed: number
  searchQuery: string
}

export function GraphCanvas({ onNodeSelect, selectedNode, isPlaying, speed, searchQuery }: GraphCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Sample dependency data
  const [nodes] = useState<Node[]>([
    { id: "react", label: "React", type: "package", x: 200, y: 150, dependencies: ["react-dom"] },
    { id: "react-dom", label: "ReactDOM", type: "package", x: 400, y: 150, dependencies: [] },
    { id: "next", label: "Next.js", type: "package", x: 300, y: 50, dependencies: ["react", "react-dom"] },
    { id: "tailwind", label: "Tailwind CSS", type: "package", x: 500, y: 100, dependencies: [] },
    { id: "app.tsx", label: "App.tsx", type: "file", x: 150, y: 250, dependencies: ["react"] },
    { id: "utils.ts", label: "utils.ts", type: "file", x: 350, y: 250, dependencies: [] },
    { id: "api.ts", label: "api.ts", type: "file", x: 450, y: 200, dependencies: ["utils.ts"] },
  ])

  const filteredNodes = nodes.filter(
    (node) => searchQuery === "" || node.label.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas size
    const container = containerRef.current
    if (container) {
      canvas.width = container.clientWidth
      canvas.height = container.clientHeight
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Apply transformations
    ctx.save()
    ctx.translate(pan.x, pan.y)
    ctx.scale(zoom, zoom)

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
    gradient.addColorStop(0, "#d97706")
    gradient.addColorStop(0.5, "#ea580c")
    gradient.addColorStop(1, "#f59e0b")

    ctx.strokeStyle = gradient
    ctx.lineWidth = 3
    ctx.shadowColor = "#ea580c"
    ctx.shadowBlur = 10

    filteredNodes.forEach((node) => {
      node.dependencies.forEach((depId) => {
        const depNode = nodes.find((n) => n.id === depId)
        if (depNode && filteredNodes.includes(depNode)) {
          ctx.beginPath()
          ctx.moveTo(node.x, node.y)
          ctx.lineTo(depNode.x, depNode.y)

          if (isPlaying) {
            ctx.setLineDash([8, 4])
            ctx.lineDashOffset = Date.now() * speed * 0.02
            ctx.shadowBlur = 15 + Math.sin(Date.now() * 0.005) * 5
          } else {
            ctx.setLineDash([])
            ctx.shadowBlur = 8
          }

          ctx.stroke()
        }
      })
    })

    ctx.shadowColor = "transparent"
    filteredNodes.forEach((node) => {
      const isSelected = node.id === selectedNode
      const isHighlighted = searchQuery !== "" && node.label.toLowerCase().includes(searchQuery.toLowerCase())

      const nodeGradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 60)
      if (isSelected) {
        nodeGradient.addColorStop(0, "rgba(217, 119, 6, 0.9)")
        nodeGradient.addColorStop(1, "rgba(234, 88, 12, 0.7)")
      } else if (isHighlighted) {
        nodeGradient.addColorStop(0, "rgba(251, 191, 36, 0.8)")
        nodeGradient.addColorStop(1, "rgba(254, 252, 232, 0.9)")
      } else {
        nodeGradient.addColorStop(0, "rgba(254, 252, 232, 0.95)")
        nodeGradient.addColorStop(1, "rgba(255, 255, 255, 0.8)")
      }

      ctx.fillStyle = nodeGradient
      ctx.strokeStyle = isSelected ? "#d97706" : isHighlighted ? "#f59e0b" : "#d1d5db"
      ctx.lineWidth = isSelected ? 4 : 2

      const width = 140
      const height = 50
      const radius = 16
      const x = node.x - width / 2
      const y = node.y - height / 2

      if (isSelected) {
        ctx.shadowColor = "#ea580c"
        ctx.shadowBlur = 20
      }

      ctx.beginPath()
      ctx.roundRect(x, y, width, height, radius)
      ctx.fill()
      ctx.stroke()

      ctx.shadowColor = "transparent"

      const textGradient = ctx.createLinearGradient(x, y, x + width, y + height)
      if (isSelected) {
        textGradient.addColorStop(0, "#ffffff")
        textGradient.addColorStop(1, "#fef3c7")
      } else {
        textGradient.addColorStop(0, "#374151")
        textGradient.addColorStop(1, "#92400e")
      }

      ctx.fillStyle = textGradient
      ctx.font = "bold 14px 'Orbitron', monospace"
      ctx.textAlign = "center"
      ctx.textBaseline = "middle"
      ctx.fillText(node.label.toUpperCase(), node.x, node.y - 8)

      ctx.fillStyle = isSelected ? "#fef3c7" : "#92400e"
      ctx.font = "11px 'Geist Sans', sans-serif"
      ctx.fillText(`⚡ ${node.type.toUpperCase()}`, node.x, node.y + 10)

      if (isSelected && isPlaying) {
        const time = Date.now() * 0.003
        for (let i = 0; i < 3; i++) {
          const pulseRadius = 70 + Math.sin(time + i * 0.5) * 15 + i * 10
          const alpha = 0.4 - i * 0.1
          ctx.strokeStyle = `rgba(217, 119, 6, ${alpha})`
          ctx.lineWidth = 3 - i
          ctx.globalAlpha = alpha
          ctx.beginPath()
          ctx.arc(node.x, node.y, pulseRadius, 0, Math.PI * 2)
          ctx.stroke()
        }
        ctx.globalAlpha = 1
      }
    })

    ctx.restore()
  }, [nodes, filteredNodes, selectedNode, searchQuery, isPlaying, speed, zoom, pan])

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left - pan.x) / zoom
    const y = (event.clientY - rect.top - pan.y) / zoom

    // Find clicked node
    const clickedNode = filteredNodes.find((node) => {
      const dx = x - node.x
      const dy = y - node.y
      return Math.abs(dx) < 60 && Math.abs(dy) < 20
    })

    if (clickedNode) {
      onNodeSelect(clickedNode.id)
    }
  }

  const handleMouseDown = (event: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true)
    setDragStart({ x: event.clientX - pan.x, y: event.clientY - pan.y })
  }

  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setPan({
        x: event.clientX - dragStart.x,
        y: event.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleZoomIn = () => setZoom((prev) => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setZoom((prev) => Math.max(prev / 1.2, 0.3))
  const handleReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-gradient-to-br from-background via-muted/10 to-accent/5 overflow-hidden"
    >
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-primary/20 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 6}s`,
              animationDuration: `${4 + Math.random() * 4}s`,
            }}
          />
        ))}
      </div>

      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="w-full h-full cursor-grab active:cursor-grabbing relative z-10"
      />

      <div className="absolute top-6 right-6 flex flex-col gap-3">
        <Button
          variant="secondary"
          size="icon"
          onClick={handleZoomIn}
          className="glass-button w-12 h-12 rounded-2xl shadow-xl"
        >
          <ZoomIn className="w-5 h-5 text-accent" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          onClick={handleZoomOut}
          className="glass-button w-12 h-12 rounded-2xl shadow-xl"
        >
          <ZoomOut className="w-5 h-5 text-accent" />
        </Button>
        <Button
          variant="secondary"
          size="icon"
          onClick={handleReset}
          className="glass-button w-12 h-12 rounded-2xl shadow-xl"
        >
          <RotateCcw className="w-5 h-5 text-accent" />
        </Button>
      </div>

      <div className="absolute bottom-6 left-6">
        <Card className="glass-card px-4 py-3 animate-glow-pulse">
          <div className="flex items-center gap-3 text-sm">
            <Sparkles className="w-4 h-4 text-accent animate-pulse" />
            <span className="text-gradient font-bold font-[family-name:var(--font-orbitron)]">
              NODES: {filteredNodes.length}
            </span>
            <span className="text-muted-foreground">|</span>
            <span className="text-gradient font-bold font-[family-name:var(--font-orbitron)]">
              ZOOM: {Math.round(zoom * 100)}%
            </span>
          </div>
        </Card>
      </div>
    </div>
  )
}
