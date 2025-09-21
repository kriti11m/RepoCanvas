import { useEffect } from 'react'

export function useCursorTrail() {
  useEffect(() => {
    let trails: HTMLElement[] = []
    let isThrottled = false

    const createTrail = (x: number, y: number) => {
      if (isThrottled) return
      
      const trail = document.createElement('div')
      trail.className = 'cursor-trail'
      trail.style.left = `${x - 6}px`
      trail.style.top = `${y - 6}px`
      
      document.body.appendChild(trail)
      trails.push(trail)

      // Remove trail after animation completes
      setTimeout(() => {
        if (trail.parentNode) {
          document.body.removeChild(trail)
        }
        trails = trails.filter(t => t !== trail)
      }, 1500)

      // Throttle trail creation to avoid too many elements
      isThrottled = true
      setTimeout(() => {
        isThrottled = false
      }, 50) // Create trail every 50ms max
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