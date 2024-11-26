import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { motion } from 'framer-motion';

const ParticleBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number; y: number; size: number; speedX: number; speedY: number }[] = [];
    
    const initParticles = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      particles = Array.from({ length: 50 }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1,
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: (Math.random() - 0.5) * 0.5
      }));
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach(particle => {
        particle.x += particle.speedX;
        particle.y += particle.speedY;

        if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    const handleResize = () => {
      initParticles();
    };

    initParticles();
    animate();

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 -z-10 pointer-events-none" />;
};

const FloatingElement = ({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) => (
  <motion.div
    initial={{ y: 20, opacity: 0 }}
    animate={{ y: 0, opacity: 1 }}
    transition={{
      duration: 0.8,
      delay,
      ease: "easeOut",
    }}
  >
    {children}
  </motion.div>
);

const LandingPage: React.FC = () => {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-gradient-to-b from-primary/5 to-primary/10">
      <ParticleBackground />
      
      <div className="relative z-10 min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center text-center px-4">
        <div className="max-w-4xl mx-auto relative">
          <FloatingElement>
            <h1 className="font-display text-6xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
              Unleash Your Story
            </h1>
          </FloatingElement>

          <FloatingElement delay={0.2}>
            <p className="font-serif text-xl md:text-2xl mb-8 max-w-2xl mx-auto text-muted-foreground">
              Craft extraordinary tales with the power of AI, where imagination meets innovation
              in a symphony of storytelling magic
            </p>
          </FloatingElement>

          <FloatingElement delay={0.4}>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/create-story" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  className="w-full sm:w-auto group relative px-8 py-6 text-lg transform transition-all duration-200 ease-out hover:scale-105 active:scale-95 bg-gradient-to-r from-primary to-purple-600 hover:from-purple-600 hover:to-primary focus:ring-2 focus:ring-primary/50 focus:outline-none"
                >
                  <span className="relative z-10 flex items-center justify-center">
                    Begin Your Journey
                    <svg 
                      className="w-5 h-5 ml-2 transform group-hover:translate-x-1 transition-transform" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M13 7l5 5m0 0l-5 5m5-5H6" 
                      />
                    </svg>
                  </span>
                </Button>
              </Link>
              <Link to="/upload-book" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto group px-8 py-6 text-lg border-2 transform transition-all duration-200 ease-out hover:scale-105 active:scale-95 hover:bg-primary/5 focus:ring-2 focus:ring-primary/50 focus:outline-none"
                >
                  <span className="flex items-center justify-center">
                    Upload Your Story
                    <svg 
                      className="w-5 h-5 ml-2 transform group-hover:translate-y-[-2px] transition-transform" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" 
                      />
                    </svg>
                  </span>
                </Button>
              </Link>
            </div>
          </FloatingElement>

          <div className="absolute -z-10 inset-0 blur-3xl opacity-20 bg-gradient-to-r from-purple-500 to-pink-500 animate-pulse" />
        </div>
      </div>

      {/* Decorative Elements */}
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-background to-transparent" />
      <div className="absolute top-1/4 left-10 w-32 h-32 bg-purple-500/10 rounded-full blur-xl animate-pulse" />
      <div className="absolute bottom-1/4 right-10 w-32 h-32 bg-pink-500/10 rounded-full blur-xl animate-pulse" />
    </div>
  );
}

export default LandingPage;
