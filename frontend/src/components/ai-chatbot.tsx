"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Send, Bot, User, Loader2, Eye, Minimize2, Maximize2 } from "lucide-react"
import { apiService, type GraphData, type ChatbotQueryResponse, type CodeSnippet } from "@/services/api"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  timestamp: Date
  showVisualize?: boolean
}

interface AIChatbotProps {
  onClose: () => void
  onGraphUpdate?: (graphData: GraphData) => void
  onResponseStatus?: (success: boolean) => void
  currentGraphData?: GraphData | null
}

export function AIChatbot({ onClose, onGraphUpdate, onResponseStatus, currentGraphData }: AIChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm your AI assistant for RepoCanvas. I can help you analyze dependencies, understand code relationships, and navigate your repository structure. What would you like to know?",
      sender: "ai",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentQuery = inputValue
    setInputValue("")
    setIsTyping(true)

    try {
      // Call the ask endpoint for chatbot responses
      const response: ChatbotQueryResponse = await apiService.queryChatbot({
        question: currentQuery
      })

      let aiContent = ""
      let showVisualize = false

      if (response.success) {
        if (response.summary) {
          aiContent = response.summary
          // If there's answer_path data, show visualize button
          if (response.answer_path && response.answer_path.length > 0) {
            showVisualize = true
            aiContent += `\n\n🔗 Found optimal path through ${response.answer_path.length} connected nodes.`
          }
        } else if (response.snippets && response.snippets.length > 0) {
          aiContent = `I found ${response.snippets.length} relevant code snippets. Here's what I discovered:\n\n`
          aiContent += response.snippets.slice(0, 3).map((snippet, index) => 
            `**${index + 1}. ${snippet.function_name || snippet.file_path}**\n` +
            `File: ${snippet.file_path}\n` +
            `${snippet.doc ? snippet.doc + '\n' : ''}`
          ).join('\n')
          
          if (response.answer_path && response.answer_path.length > 0) {
            showVisualize = true
            aiContent += `\n\n🔗 Found optimal path through ${response.answer_path.length} connected nodes.`
          }
        } else {
          aiContent = "I couldn't find specific information for your query. Try rephrasing your question or make sure the repository has been analyzed."
        }
        
        if (response.processing_time) {
          aiContent += `\n\n⚡ Processing time: ${response.processing_time.toFixed(2)}s`
        }
      } else {
        let errorMessage = "Sorry, I encountered an error processing your query."
        
        if (response.error) {
          if (response.error.includes("Collection") && response.error.includes("empty")) {
            errorMessage = "The repository hasn't been fully indexed yet. Please wait for the analysis to complete, or try analyzing the repository again."
          } else if (response.error.includes("vectors are not indexed yet")) {
            errorMessage = "The repository data exists but vectors are still being indexed. This usually takes a few minutes after analysis completes. Please wait a moment and try again."
          } else if (response.error.includes("Search failed")) {
            errorMessage = "Search service is temporarily unavailable. The repository analysis completed, but search functionality needs to be restarted."
          } else {
            errorMessage = `Error: ${response.error}`
          }
        }
        
        aiContent = errorMessage
      }

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: aiContent,
        sender: "ai",
        timestamp: new Date(),
        showVisualize
      }

      setMessages((prev) => [...prev, aiResponse])
      onResponseStatus?.(response.success)
      
      // Store response data for visualization
      if (response.success && response.answer_path && onGraphUpdate) {
        // Store the graph data but don't update immediately
        (aiResponse as any).graphData = {
          nodes: response.answer_path,
          edges: response.path_edges || []
        }
      }
      
    } catch (error: any) {
      console.error('Chatbot error:', error)
      
      let errorMessage = "Sorry, I encountered an error. "
      
      if (error.message.includes("Failed to process")) {
        errorMessage += "The search service may need to be restarted. Please try analyzing the repository again."
      } else if (error.message.includes("not available")) {
        errorMessage += "Please make sure the repository has been analyzed first."
      } else {
        errorMessage += error.message
      }
      
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: errorMessage,
        sender: "ai",
        timestamp: new Date(),
      }
      
      setMessages((prev) => [...prev, errorResponse])
      onResponseStatus?.(false)
    } finally {
      setIsTyping(false)
    }
  }

  const handleVisualize = (message: Message) => {
    if ((message as any).graphData && onGraphUpdate && currentGraphData) {
      const pathData = (message as any).graphData
      const pathNodeIds = new Set(pathData.nodes) // nodes are just IDs from answer_path
      
      // Filter current graph data to only include path nodes
      const pathNodes = currentGraphData.nodes.filter(node => pathNodeIds.has(node.id))
      const pathEdges = pathData.edges || [] // Use edges from path computation
      
      // Create filtered graph data for visualization
      const filteredGraphData: GraphData = {
        nodes: pathNodes,
        edges: pathEdges
      }
      
      onGraphUpdate(filteredGraphData)
      // Minimize the chatbot after visualization
      setIsMinimized(true)
    }
  }

  const formatMessageContent = (content: string) => {
    return content.split('\n').map((line, index) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return <div key={index} className="font-bold text-primary mb-2">{line.slice(2, -2)}</div>
      }
      if (line.startsWith('💡') || line.startsWith('⚡') || line.startsWith('🔍') || line.startsWith('📍') || line.startsWith('🔗')) {
        return <div key={index} className="text-accent mb-1">{line}</div>
      }
      return <div key={index} className="mb-1">{line}</div>
    })
  }

  // Minimized view
  if (isMinimized) {
    return (
      <>
        {/* Background blur */}
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40" />
        
        {/* Minimized chatbot */}
        <div className="fixed bottom-6 right-6 z-50">
          <Button
            onClick={() => setIsMinimized(false)}
            className="glass-card border-2 border-primary/30 shadow-xl p-4 animate-glow-pulse"
          >
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-accent" />
              <span className="font-bold text-gradient">AI ASSISTANT</span>
              <Maximize2 className="w-4 h-4 ml-2" />
            </div>
          </Button>
        </div>
      </>
    )
  }

  // Full chatbot view
  return (
    <>
      {/* Background blur */}
      <div className="fixed inset-0 bg-black/30 backdrop-blur-md z-40" onClick={onClose} />
      
      {/* Centered chatbot */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-6">
        <Card className="w-full max-w-2xl h-[600px] glass-card border-2 border-primary/30 shadow-2xl animate-slide-in animate-glow-pulse shadow-primary/20 glow-border">
          <CardHeader className="pb-3 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-primary to-accent rounded-xl">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <CardTitle className="text-xl font-bold text-gradient font-[family-name:var(--font-orbitron)] tracking-wide">
                  AI ASSISTANT
                </CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => setIsMinimized(true)} 
                  className="glass-button"
                >
                  <Minimize2 className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={onClose} className="glass-button">
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="p-0 flex flex-col h-[calc(100%-80px)]">
            {/* Scrollable Messages Area */}
            <ScrollArea className="flex-1 px-6 py-2">
              <div className="space-y-4 pb-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[80%] ${message.sender === "user" ? "order-2" : "order-1"}`}>
                      <div
                        className={`p-4 rounded-2xl break-words ${
                          message.sender === "user"
                            ? "bg-primary text-primary-foreground ml-4"
                            : "bg-muted/50 glass-card minecraft-border mr-4"
                        }`}
                      >
                        <div className="text-sm whitespace-pre-wrap leading-relaxed overflow-hidden">
                          {formatMessageContent(message.content)}
                        </div>
                        
                        {/* Simple Visualize button */}
                        {message.sender === "ai" && message.showVisualize && (
                          <Button
                            onClick={() => handleVisualize(message)}
                            size="sm"
                            className="mt-4 bg-accent hover:bg-accent/80 text-accent-foreground minecraft-border font-bold"
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            Visualize Path
                          </Button>
                        )}
                      </div>
                      <div className={`flex items-center gap-2 mt-2 text-xs text-muted-foreground ${
                        message.sender === "user" ? "justify-end" : "justify-start"
                      }`}>
                        {message.sender === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Typing indicator */}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-muted/50 glass-card minecraft-border p-3 rounded-2xl mr-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Thinking...
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            
            {/* Fixed Input Area */}
            <div className="p-6 border-t border-muted/20 flex-shrink-0 bg-background/95 backdrop-blur-sm">
              <div className="flex gap-3">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask about your repository..."
                  className="glass-card minecraft-border bg-muted/10 flex-1"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  disabled={isTyping}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isTyping || !inputValue.trim()}
                  className="glass-button minecraft-border px-4 flex-shrink-0"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}