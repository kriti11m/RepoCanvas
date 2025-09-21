import { useEffect } from 'react'

export function useCursorTrail() {
  useEffect(() => {
    let trails: HTMLElement[] = []
    let isThrottled = false
    let trailIndex = 0

    const createTrail = (x: number, y: number) => {
      if (isThrottled) return
      
      const trail = document.createElement('div')
      trail.className = 'cursor-trail'
      
      // Add slight randomization for more organic feel
      const offsetX = (Math.random() - 0.5) * 4
      const offsetY = (Math.random() - 0.5) * 4
      
      trail.style.left = `${x - 8 + offsetX}px`
      trail.style.top = `${y - 8 + offsetY}px`
      
      // Add variety to the trails
      const variations = [
        'rgba(0, 255, 136, 0.9)',
        'rgba(0, 153, 255, 0.8)',
        'rgba(138, 43, 226, 0.7)',
        'rgba(255, 20, 147, 0.6)'
      ]
      
      const colorIndex = trailIndex % variations.length
      trail.style.background = `linear-gradient(45deg, ${variations[colorIndex]}, ${variations[(colorIndex + 1) % variations.length]})`
      
      // Add slight scale variation
      const scale = 0.8 + Math.random() * 0.4
      trail.style.transform = `scale(${scale})`
      
      document.body.appendChild(trail)
      trails.push(trail)
      trailIndex++

      // Remove trail after animation completes
      setTimeout(() => {
        if (trail.parentNode) {
          document.body.removeChild(trail)
        }
        trails = trails.filter(t => t !== trail)
      }, 2000)

      // Throttle trail creation for smooth performance
      isThrottled = true
      setTimeout(() => {
        isThrottled = false
      }, 30) // Create trail every 30ms for smoother effect
    }

    const handleMouseMove = (e: MouseEvent) => {
      createTrail(e.clientX, e.clientY)
    }

    // Add event listener
    document.addEventListener('mousemove', handleMouseMove, { passive: true })

    // Cleanup function
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      // Clean up any remaining trails
      trails.forEach(trail => {
        if (trail.parentNode) {
          document.body.removeChild(trail)
        }
      })
      trails = []
    }
  }, [])
}