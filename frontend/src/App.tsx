import { useState } from 'react'
import { motion } from 'framer-motion'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import BackgroundRippleEffect from './components/ui/background-ripple-effect'
import FuturisticHero from './components/ui/futuristic-hero'
import FeaturesBento from './components/ui/features-bento'
import { TestimonialsSection } from './components/ui/testimonials-with-marquee'
import { GradientButton } from './components/ui/gradient-button'
import WorkflowSection from './components/ui/workflow-section'
import { DashboardPage } from './components/DashboardPage'
import { AboutPage } from './components/AboutPage'
import { SettingsPage } from './components/SettingsPage'
import { ErrorPage } from './components/ErrorPage'
import { SettingsProvider } from './lib/settings-context'

function HomePage() {
  const [, setActiveSection] = useState('home')

  // Scroll to section function
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
    setActiveSection(sectionId);
  };

  // Sample testimonials data
  const testimonials = [
    {
      author: {
        name: "Sarah Johnson",
        handle: "Data Analyst @ TechCorp",
        avatar: "https://randomuser.me/api/portraits/women/44.jpg"
      },
      text: "This tool transformed how I analyze data. Now I can query our database using plain English instead of complex SQL!"
    },
    {
      author: {
        name: "Michael Chen",
        handle: "Product Manager",
        avatar: "https://randomuser.me/api/portraits/men/32.jpg"
      },
      text: "As a non-technical PM, I can now get data insights without bothering our engineers. Game changer!"
    },
    {
      author: {
        name: "Lisa Rodriguez",
        handle: "Business Analyst",
        avatar: "https://randomuser.me/api/portraits/women/65.jpg"
      },
      text: "The SQL explanations help me learn while using the tool. I've improved my query skills just by using this daily."
    },
    {
      author: {
        name: "David Kim",
        handle: "Database Administrator",
        avatar: "https://randomuser.me/api/portraits/men/11.jpg"
      },
      text: "Even as a DB admin, I use this to quickly prototype queries. The optimized SQL it generates is surprisingly good."
    }
  ]

  return (
    <div className="relative w-full min-h-screen bg-black text-white overflow-x-hidden">
      {/* Background Effect */}
      <BackgroundRippleEffect />
      
      <main className="flex flex-col w-full">
        {/* Hero Section with the new FuturisticHero component */}
        <FuturisticHero 
          subtitle="Ask questions in plain English and get optimized SQL instantly. Powered by AI and PydanticAI."
        >
          <div className="flex flex-col sm:flex-row gap-4">
            <Link to="/dashboard">
            <GradientButton>
              Try Demo
            </GradientButton>
            </Link>
            <GradientButton 
              variant="variant" 
              onClick={() => scrollToSection('how-it-works')}
            >
              How It Works
            </GradientButton>
          </div>
        </FuturisticHero>

        {/* Features Section */}
        <FeaturesBento />
        
        {/* How It Works Section */}
        <WorkflowSection />
        
        {/* Testimonials - no top padding needed */}
        <TestimonialsSection
          title="Trusted by Data Teams Everywhere"
          description="See what our users have to say about their experience with Agentic Text2SQL"
          testimonials={testimonials}
          className="pt-0 pb-20"
        />
        
        {/* CTA Section */}
        <section className="relative py-20 overflow-hidden">
          <div className="container mx-auto max-w-4xl text-center z-10 relative" style={{ position: 'relative' }}>
            <motion.h2 
              className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
            >
              Ready to Revolutionize Your Data Access?
            </motion.h2>
            <motion.p 
              className="text-lg text-white/70 mb-8 max-w-2xl mx-auto"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              viewport={{ once: true }}
            >
              Start using Agentic Text2SQL today and empower your entire team with instant database insights - no SQL expertise required.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              viewport={{ once: true }}
              className="flex justify-center"
            >
              <Link to="/dashboard">
              <GradientButton size="lg">
                Get Started Now
              </GradientButton>
              </Link>
            </motion.div>
          </div>
          
          {/* Decorative elements */}
          <div className="absolute -bottom-48 -left-48 w-96 h-96 bg-purple-500/30 rounded-full filter blur-3xl"></div>
          <div className="absolute -top-48 -right-48 w-96 h-96 bg-blue-500/20 rounded-full filter blur-3xl"></div>
        </section>
      </main>
    </div>
  )
}

function App() {
  return (
    <SettingsProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<ErrorPage />} />
        </Routes>
      </Router>
    </SettingsProvider>
  )
}

export default App
