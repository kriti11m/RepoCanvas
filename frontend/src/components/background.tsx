export function CyberBackground() {
  return (
    <div
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{
        background: 'linear-gradient(135deg, #000011 0%, #001122 100%)',
        backgroundImage: 'linear-gradient(rgba(0, 153, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 153, 255, 0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }}
    />
  )
}