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
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50 animate-bounce-in">
      <Card className="glass-card px-6 py-4 shadow-2xl border-0 rounded-3xl animate-glow-pulse">
        <div className="flex items-center gap-8">
          {/* Playback Controls */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="w-10 h-10 rounded-2xl hover:bg-primary/20 transition-all duration-300"
            >
              <SkipBack className="w-5 h-5 text-accent" />
            </Button>

            <Button
              onClick={onPlayPause}
              size="icon"
              className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-accent hover:from-accent hover:to-primary text-white shadow-xl transform hover:scale-110 transition-all duration-300"
            >
              {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="w-10 h-10 rounded-2xl hover:bg-primary/20 transition-all duration-300"
            >
              <SkipForward className="w-5 h-5 text-accent" />
            </Button>
          </div>

          {/* Speed Control */}
          <div className="flex items-center gap-4">
            <Label
              htmlFor="speed"
              className="text-sm font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-2"
            >
              <Zap className="w-4 h-4" />
              SPEED
            </Label>
            <div className="w-24 relative">
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
            <span className="text-sm font-bold text-gradient font-[family-name:var(--font-orbitron)] font-mono w-10">
              {speed[0].toFixed(1)}X
            </span>
          </div>

          {/* Demo Mode Toggle */}
          <div className="flex items-center gap-3">
            <Switch
              id="demo-mode"
              checked={isDemoMode}
              onCheckedChange={onDemoModeChange}
              className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-primary data-[state=checked]:to-accent"
            />
            <Label
              htmlFor="demo-mode"
              className="text-sm font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 animate-pulse" />
              DEMO MODE
            </Label>
          </div>
        </div>
      </Card>
    </div>
  )
}
