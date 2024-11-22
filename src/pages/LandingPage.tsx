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

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: { x: number; y: number; size: number; speedX: number; speedY: number }[] = [];
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1,
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: (Math.random() - 0.5) * 0.5
      });
    }

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

      requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 -z-10" />;
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
      
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
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
              <Link to="/create-story">
                <Button
                  size="lg"
                  className="group relative px-8 py-6 text-lg hover:scale-105 transition-transform duration-200 bg-gradient-to-r from-primary to-purple-600 hover:from-purple-600 hover:to-primary"
                >
                  <span className="relative z-10">Begin Your Journey</span>
                </Button>
              </Link>
              <Link to="/upload-book">
                <Button
                  size="lg"
                  variant="outline"
                  className="group px-8 py-6 text-lg border-2 hover:scale-105 transition-transform duration-200"
                >
                  Upload Your Story
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
