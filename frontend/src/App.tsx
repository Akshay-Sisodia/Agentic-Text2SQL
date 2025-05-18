// React and third-party imports
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { SettingsProvider } from '@/lib/settings-context'

// Page components
import { DashboardPage } from './components/DashboardPage'
import { AboutPage } from './components/AboutPage'
import { SettingsPage } from './components/SettingsPage'
import { ErrorPage } from './components/ErrorPage'
import { LoginPage } from './components/LoginPage'

// UI components
import BackgroundRippleEffect from './components/ui/background-ripple-effect'
import FuturisticHero from './components/ui/futuristic-hero'
import FeaturesBento from './components/ui/features-bento'
import { TestimonialsSection } from './components/ui/testimonials-with-marquee'
import { GradientButton } from './components/ui/gradient-button'
import WorkflowSection from './components/ui/workflow-section'

// Testimonials data
import { testimonials } from './data/testimonials'

function HomePage() {
  const [activeSection, setActiveSection] = useState('home');

  // Scroll to section function
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
    setActiveSection(sectionId);
  };
  
  // Update page title for SEO
  useEffect(() => {
    document.title = "Agentic Text2SQL | Natural Language to SQL Database Queries";
    
    // Update meta description
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'Transform natural language questions into powerful, optimized SQL queries. No technical expertise required. Simplify database access with intelligent natural language processing.');
    } else {
      const meta = document.createElement('meta');
      meta.name = 'description';
      meta.content = 'Transform natural language questions into powerful, optimized SQL queries. No technical expertise required. Simplify database access with intelligent natural language processing.';
      document.head.appendChild(meta);
    }
    
    // Add keywords meta tag
    const metaKeywords = document.createElement('meta');
    metaKeywords.name = 'keywords';
    metaKeywords.content = 'text to SQL, natural language processing, database queries, SQL generation, data analytics';
    document.head.appendChild(metaKeywords);
  }, []);

  return (
    <div className="relative w-full min-h-screen bg-black text-white overflow-x-hidden">
      {/* Background Effect */}
      <BackgroundRippleEffect />
      
      <main className="flex flex-col w-full">
        {/* Hero Section with the new FuturisticHero component */}
        <FuturisticHero 
          subtitle="Transform natural language into optimized SQL queries instantly. Database insights without the technical complexity."
        >
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/dashboard">
              <GradientButton>
                Try Demo
              </GradientButton>
            </Link>
            <GradientButton 
              variant="variant" 
              onClick={() => scrollToSection('how-it-works')}
              aria-label="View how it works section"
              title="View how it works section"
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
        <section className="relative py-12 md:py-20 px-4 overflow-hidden">
          <div className="container mx-auto max-w-4xl text-center z-10 relative" style={{ position: 'relative' }}>
            <motion.h2 
              className="text-3xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent mb-4 md:mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
            >
              Ready to Revolutionize Your Data Access?
            </motion.h2>
            <motion.p 
              className="text-base md:text-lg text-white/70 mb-6 md:mb-8 max-w-2xl mx-auto"
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
                <GradientButton size="lg" aria-label="Get started with the application" title="Get started with the application">
                  Get Started Now
                </GradientButton>
              </Link>
            </motion.div>
          </div>
          
          {/* Decorative elements */}
          <div className="absolute -bottom-48 -left-48 w-72 md:w-96 h-72 md:h-96 bg-purple-500/30 rounded-full filter blur-3xl"></div>
          <div className="absolute -top-48 -right-48 w-72 md:w-96 h-72 md:h-96 bg-blue-500/20 rounded-full filter blur-3xl"></div>
        </section>
      </main>
    </div>
  );
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
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<ErrorPage />} />
        </Routes>
      </Router>
    </SettingsProvider>
  );
}

export default App;
