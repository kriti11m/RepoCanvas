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
    <div className="z-60 animate-bounce-in">
      <Card className="glass-card px-3 py-1.5 shadow-2xl border-0 rounded-xl animate-glow-pulse">
        <div className="flex items-center gap-2">
          {/* Playback Controls */}
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="w-7 h-7 rounded-lg hover:bg-primary/20 transition-all duration-300"
            >
              <SkipBack className="w-3 h-3 text-accent" />
            </Button>

            <Button
              onClick={onPlayPause}
              size="icon"
              className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent hover:from-accent hover:to-primary text-white shadow-lg transform hover:scale-105 transition-all duration-300"
            >
              {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 ml-0.5" />}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="w-7 h-7 rounded-lg hover:bg-primary/20 transition-all duration-300"
            >
              <SkipForward className="w-3 h-3 text-accent" />
            </Button>
          </div>

          {/* Speed Control */}
          <div className="flex items-center gap-1">
            <Label
              htmlFor="speed"
              className="text-xs font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-0.5"
            >
              <Zap className="w-2.5 h-2.5" />
              SPEED
            </Label>
            <div className="w-12 relative">
              <Slider
                id="speed"
                min={0.1}
                max={3}
                step={0.1}
                value={speed}
                onValueChange={(value) => {
                  console.log("Speed changed:", value);
                  onSpeedChange(value);
                }}
                className="w-full [&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-primary [&_[role=slider]]:to-accent [&_[role=slider]]:border-0 [&_[role=slider]]:shadow-lg [&_[role=slider]]:w-4 [&_[role=slider]]:h-4"
              />
            </div>
            <span className="text-xs font-bold text-gradient font-mono w-6">
              {speed[0].toFixed(1)}X
            </span>
          </div>

          {/* Demo Mode Toggle */}
          <div className="flex items-center gap-1">
            <Switch
              id="demo-mode"
              checked={isDemoMode}
              onCheckedChange={(checked) => {
                console.log("Demo mode changed:", checked);
                onDemoModeChange(checked);
              }}
              className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-primary data-[state=checked]:to-accent scale-75"
            />
            <Label
              htmlFor="demo-mode"
              className="text-xs font-bold text-gradient font-[family-name:var(--font-orbitron)] whitespace-nowrap flex items-center gap-0.5"
            >
              <Sparkles className="w-2.5 h-2.5 animate-pulse" />
              DEMO
            </Label>
          </div>
        </div>
      </Card>
    </div>
  )
}
