"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Play, Pause, SkipBack, SkipForward, Zap, Sparkles } from "lucide-react"

interface ControlsBarProps {
  isPlaying: boolean
  onPlayPause: () => void
  speed: number[]
  onSpeedChange: (speed: number[]) => void
  isDemoMode: boolean
  onDemoModeChange: (enabled: boolean) => void
}

export function ControlsBar({
  isPlaying,
  onPlayPause,
  speed,
  onSpeedChange,
  isDemoMode,
  onDemoModeChange,
}: ControlsBarProps) {
  return (
    <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 animate-bounce-in">
      <Card className="glass-card px-4 py-2 shadow-2xl border-0 rounded-2xl animate-glow-pulse">
        <div className="flex items-center gap-4">
          {/* Playback Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="w-8 h-8 rounded-xl hover:bg-primary/20 transition-all duration-300"
            >
              <SkipBack className="w-4 h-4 text-accent" />
            </Button>

            <Button
              onClick={onPlayPause}
              size="icon"
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent hover:from-accent hover:to-primary text-white shadow-xl transform hover:scale-110 transition-all duration-300"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="w-8 h-8 rounded-xl hover:bg-primary/20 transition-all duration-300"
            >
              <SkipForward className="w-4 h-4 text-accent" />
            </Button>
          </div>

          {/* Speed Control */}
          <div className="flex items-center gap-2">
            <Label
              htmlFor="speed"
              className="text-xs font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-1"
            >
              <Zap className="w-3 h-3" />
              SPEED
            </Label>
            <div className="w-16 relative">
              <Slider
                id="speed"
                min={0.1}
                max={3}
                step={0.1}
                value={speed}
                onValueChange={onSpeedChange}
                className="w-full [&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-primary [&_[role=slider]]:to-accent [&_[role=slider]]:border-0 [&_[role=slider]]:shadow-lg"
              />
            </div>
            <span className="text-xs font-bold text-gradient font-[family-name:var(--font-orbitron)] font-mono w-8">
              {speed[0].toFixed(1)}X
            </span>
          </div>

          {/* Demo Mode Toggle */}
          <div className="flex items-center gap-2">
            <Switch
              id="demo-mode"
              checked={isDemoMode}
              onCheckedChange={onDemoModeChange}
              className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-primary data-[state=checked]:to-accent scale-75"
            />
            <Label
              htmlFor="demo-mode"
              className="text-xs font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3 animate-pulse" />
              DEMO MODE
            </Label>
          </div>
        </div>
      </Card>
    </div>
  )
}
