"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Send, Bot, User } from "lucide-react"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  timestamp: Date
}

interface AIChatbotProps {
  onClose: () => void
}

export function AIChatbot({ onClose }: AIChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your AI assistant for RepoCanvas. I can help you analyze dependencies, understand code relationships, and navigate your repository structure. What would you like to know?",
      sender: "ai",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateAIResponse(inputValue),
        sender: "ai",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiResponse])
      setIsTyping(false)
    }, 1500)
  }

  const generateAIResponse = (userInput: string): string => {
    const responses = [
      "Based on your repository analysis, I can see several interesting dependency patterns. Would you like me to explain the critical paths?",
      "That's a great question! The dependency graph shows some potential optimization opportunities. Let me break down the key areas for you.",
      "I notice you're looking at the node relationships. The current structure suggests a modular architecture with some circular dependencies that might need attention.",
      "From the code analysis, I can identify several performance bottlenecks and suggest improvements. Would you like me to prioritize them?",
      "The repository structure indicates a well-organized codebase. I can help you understand the component relationships and suggest refactoring opportunities.",
    ]
    return responses[Math.floor(Math.random() * responses.length)]
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl h-[600px] glass-card border-0 shadow-2xl animate-slide-in-up minecraft-border">
        <CardHeader className="pb-4 border-b border-primary/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary to-accent rounded-xl flex items-center justify-center minecraft-border">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <CardTitle className="text-xl font-bold text-gradient font-[family-name:var(--font-orbitron)] minecraft-text">
                AI ASSISTANT
              </CardTitle>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="glass-card w-10 h-10 hover:bg-red-500/20 minecraft-border"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-0 flex flex-col h-[calc(100%-80px)]">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.sender === "ai" && (
                    <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center flex-shrink-0 minecraft-border">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] p-3 rounded-2xl minecraft-border ${
                      message.sender === "user"
                        ? "bg-primary/20 text-primary-foreground ml-auto"
                        : "bg-muted/50 text-foreground"
                    }`}
                  >
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <span className="text-xs opacity-60 mt-1 block">{message.timestamp.toLocaleTimeString()}</span>
                  </div>
                  {message.sender === "user" && (
                    <div className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-lg flex items-center justify-center flex-shrink-0 minecraft-border">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              ))}
              {isTyping && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center flex-shrink-0 minecraft-border">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-muted/50 p-3 rounded-2xl minecraft-border">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-accent rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-accent rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-accent rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="p-4 border-t border-primary/20">
            <div className="flex gap-2">
              <Input
                placeholder="Ask me about your repository..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                className="glass-card border-primary/30 focus:border-accent focus:ring-accent/50 minecraft-border"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="glass-button px-4 minecraft-border"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
