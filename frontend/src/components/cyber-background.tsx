import { Canvas } from "@react-three/fiber"
import { OrbitControls, Stars } from "@react-three/drei"
import { useRef, useMemo } from "react"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"

function AnimatedMesh() {
  const meshRef = useRef<THREE.Mesh>(null)
  
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(1, 0), [])

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * 0.2
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.3
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.5
    }
  })

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial color="#0099ff" wireframe />
    </mesh>
  )
}

function CyberGrid() {
  const meshRef = useRef<THREE.Mesh>(null)
  const linesRef = useRef<THREE.Group>(null)

  // Create grid lines
  const gridLines = useMemo(() => {
    const lines = []
    const size = 50
    const divisions = 20
    const step = size / divisions
    const colorCenters = new THREE.Color("#0099ff")
    const colorGrid = new THREE.Color("#003366")

    // Create horizontal and vertical lines
    for (let i = 0; i <= divisions; i++) {
      const color = i === divisions / 2 ? colorCenters : colorGrid
      
      // Horizontal line
      lines.push(
        <line key={`h-${i}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([-size / 2, 0, i * step - size / 2, size / 2, 0, i * step - size / 2])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color={color} />
        </line>
      )
      
      // Vertical line
      lines.push(
        <line key={`v-${i}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([i * step - size / 2, 0, -size / 2, i * step - size / 2, 0, size / 2])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color={color} />
        </line>
      )
    }

    return lines
  }, [])

  useFrame((state) => {
    if (linesRef.current) {
      linesRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.1) * 0.1
    }
  })

  return (
    <group ref={linesRef} position={[0, -2, 0]}>
      {gridLines}
    </group>
  )
}

export function CyberBackground() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <div 
        className="absolute inset-0" 
        style={{
          background: 'linear-gradient(135deg, #000011 0%, #001122 100%)',
        }}
      />
      
      {/* Animated grid overlay */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 153, 255, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 153, 255, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          animation: 'grid-move 20s linear infinite'
        }}
      />

      <Canvas
        camera={{ position: [0, 0, 10] }}
        className="opacity-20"
      >
        <ambientLight intensity={0.1} />
        <pointLight position={[10, 10, 10]} intensity={0.3} color="#00ccff" />
        <Stars 
          radius={100}
          depth={50}
          count={5000}
          factor={4}
          saturation={0}
          fade
          speed={1}
        />
        <AnimatedMesh />
        <CyberGrid />
        <OrbitControls 
          enableZoom={false} 
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>
    </div>
  )
}