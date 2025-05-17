'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Menu, X } from 'lucide-react';

// Simplified navbar items with only essential navigation
const navItems = [
  {
    label: 'Home',
    href: '#',
  },
  {
    label: 'Features',
    href: '#features',
  },
  {
    label: 'How It Works',
    href: '#how-it-works',
  },
];

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll event to change navbar appearance
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 10) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Function to handle smooth scrolling to sections
  const scrollToSection = (href: string) => {
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setMobileMenuOpen(false);
    }
  };

  return (
    <motion.header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled 
          ? "bg-black/80 backdrop-blur-xl border-b border-white/10 py-3"
          : "bg-transparent py-5"
      )}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      <div className="container mx-auto px-4 md:px-6">
        <nav className="flex items-center justify-between">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2" onClick={(e) => { e.preventDefault(); scrollToSection('#'); }}>
            <motion.div 
              className="relative w-8 h-8 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-lg overflow-hidden"
              whileHover={{ scale: 1.1, rotate: 5 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              <motion.div 
                className="absolute inset-0 bg-gradient-to-tr from-blue-400 to-purple-600"
                animate={{ 
                  rotate: [0, 360],
                }}
                transition={{ 
                  duration: 10, 
                  repeat: Infinity, 
                  ease: "linear" 
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center text-white font-bold text-lg">
                A
              </div>
            </motion.div>
            <motion.span 
              className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent"
              whileHover={{ scale: 1.05 }}
            >
              Agentic SQL
            </motion.span>
          </a>

          {/* Desktop Navigation - Simplified with only essential links */}
          <div className="hidden md:flex items-center gap-6">
            <ul className="flex items-center gap-6">
              {navItems.map((item) => (
                <li key={item.label}>
                  <motion.a 
                    href={item.href} 
                    className="px-3 py-2 rounded-lg text-white/90 hover:text-white hover:bg-white/5 transition-colors flex items-center"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={(e) => { e.preventDefault(); scrollToSection(item.href); }}
                  >
                    {item.label}
                  </motion.a>
                </li>
              ))}
            </ul>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden">
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg bg-white/5 text-white hover:bg-white/10 transition-colors"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </nav>
      </div>

      {/* Mobile Menu - Simplified with only essential links */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            className="fixed inset-0 top-[64px] bg-black/95 backdrop-blur-lg z-40 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <nav className="container mx-auto px-4 py-6">
              <ul className="flex flex-col gap-4">
                {navItems.map((item, index) => (
                  <motion.li 
                    key={item.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <a 
                      href={item.href} 
                      className="block py-3 text-white font-semibold border-b border-white/10 hover:text-purple-400 transition-colors"
                      onClick={(e) => { e.preventDefault(); scrollToSection(item.href); }}
                    >
                      {item.label}
                    </a>
                  </motion.li>
                ))}
              </ul>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
} 