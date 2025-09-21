import { Canvas } from "@react-three/fiber"
import { OrbitControls, Stars } from "@react-three/drei"
import { useRef, useMemo, useEffect } from "react"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"

function CyberGrid() {
  const meshRef = useRef<THREE.Mesh>(null)
  const linesRef = useRef<THREE.Group>(null)

  // Create grid lines
  const gridLines = useMemo(() => {
    console.log("Creating grid lines")
    const lines = []
    const size = 50
    const divisions = 20
    const step = size / divisions

    // Horizontal lines
    for (let i = 0; i <= divisions; i++) {
      const y = i * step - size / 2
      lines.push(
        <line key={`h-${i}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([-size / 2, y, 0, size / 2, y, 0])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#00ffff" opacity={0.5} transparent />
        </line>,
      )
    }

    // Vertical lines
    for (let i = 0; i <= divisions; i++) {
      const x = i * step - size / 2
      lines.push(
        <line key={`v-${i}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([x, -size / 2, 0, x, size / 2, 0])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#00ffff" opacity={0.5} transparent />
        </line>,
      )
    }

    console.log(`Created ${lines.length} grid lines`)
    return lines
  }, [])

  useFrame((state) => {
    if (linesRef.current) {
      linesRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.1) * 0.1
    }
  })

  return (
    <group ref={linesRef} position={[0, 0, -10]}>
      {gridLines}
    </group>
  )
}

function FloatingCubes() {
  const cubesRef = useRef<THREE.Group>(null)

  const cubes = useMemo(() => {
    console.log("Creating floating cubes")
    const cubeArray = []
    for (let i = 0; i < 20; i++) {
      cubeArray.push({
        position: [(Math.random() - 0.5) * 40, (Math.random() - 0.5) * 40, (Math.random() - 0.5) * 20],
        rotation: [Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI],
        scale: Math.random() * 0.5 + 0.2,
      })
    }
    console.log(`Created ${cubeArray.length} floating cubes`)
    return cubeArray
  }, [])

  useFrame((state) => {
    if (cubesRef.current) {
      cubesRef.current.children.forEach((cube, i) => {
        cube.rotation.x += 0.01 * (i % 2 === 0 ? 1 : -1)
        cube.rotation.y += 0.01 * (i % 3 === 0 ? 1 : -1)
        cube.position.y += Math.sin(state.clock.elapsedTime + i) * 0.01
      })
    }
  })

  return (
    <group ref={cubesRef}>
      {cubes.map((cube, i) => (
        <mesh key={i} position={cube.position as [number, number, number]} scale={cube.scale}>
          <boxGeometry args={[1, 1, 1]} />
          <meshBasicMaterial color="#00ff88" wireframe opacity={0.6} transparent />
        </mesh>
      ))}
    </group>
  )
}

export function CyberBackground() {
  console.log("CyberBackground component rendering")
  
  useEffect(() => {
    console.log("CyberBackground useEffect mounted")
    console.log("Checking if three.js is loaded:", typeof THREE)
    console.log("Checking Canvas:", Canvas)
    console.log("Checking OrbitControls:", OrbitControls)
    console.log("Checking Stars:", Stars)
  }, [])
  
  return (
    <div className="fixed inset-0 z-0">
      <Canvas camera={{ position: [0, 0, 10], fov: 75 }}>
        <ambientLight intensity={0.8} />
        <pointLight position={[10, 10, 10]} intensity={1.2} />

        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

        <CyberGrid />
        <FloatingCubes />

        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.8} />
      </Canvas>
    </div>
  )
}