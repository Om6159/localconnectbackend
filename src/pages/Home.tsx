import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, ArrowRight } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { ShinyButton } from '@/components/ui/shiny-button';
import { Logo } from '@/components/ui/Logo';
import { DynamicSupportingText } from '@/components/common/DynamicSupportingText';

import '@fontsource/instrument-serif/400.css';
import '@fontsource/instrument-serif/400-italic.css';

const EXAMPLE_NEEDS = [
  "Find a maths tutor for Class 10",
  "Need an emergency electrician",
  "Looking for a wedding photographer",
  "Freelance UI designer for a startup",
];

const DISCOVERY_CATEGORIES = [
  { id: '1', title: 'Home Maintenance', count: '120+ providers', icon: '🔧' },
  { id: '2', title: 'Education & Tutors', count: '85+ providers', icon: '📚' },
  { id: '3', title: 'Creative & Tech', count: '200+ providers', icon: '💻' },
  { id: '4', title: 'Events & Catering', count: '60+ providers', icon: '🎉' },
];

export function Home() {
  const [needQuery, setNeedQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (needQuery.trim()) {
      // Mock navigation for Phase 1 as requested
      navigate('/need/understanding');
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col selection:bg-primary-soft selection:text-primary">
      {/* Top minimal bar (mobile-only, desktop uses Navbar) */}
      <div className="md:hidden flex items-center justify-between p-4 border-b border-border">
        <Logo className="h-11 w-auto" />
        <div className="flex items-center gap-1.5 text-text-caption text-muted-foreground bg-secondary px-3 py-1.5 rounded-full">
          <MapPin className="w-3 h-3" />
          <span>Local Area</span>
        </div>
      </div>

      <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-section-1 lg:px-section-2 pb-section-3">
        
        {/* Centered Editorial Hero Section */}
        <section className="pt-section-1 md:pt-hero-1 lg:pt-hero-2 pb-section-1 flex flex-col items-center text-center">
          
          {/* Primary Tagline */}
          <h1 className="font-serif font-normal text-primary text-[42px] sm:text-[52px] md:text-[72px] lg:text-[88px] tracking-normal leading-[1.1] mb-8">
            Need &rarr; Match &rarr; Connect
          </h1>
          
          {/* Animated Supporting Text */}
          <DynamicSupportingText />

          {/* Secondary Supporting Copy */}
          <p 
            className="text-[17px] sm:text-[19px] md:text-[21px] lg:text-[24px] leading-[1.55] md:leading-[1.45] text-muted-foreground font-medium max-w-[850px] text-center mx-auto mt-6 mb-16"
            style={{ fontFamily: '"Urbanist Variable", sans-serif' }}
          >
            The simplest way to discover local talent. From home repairs to specialized tutoring, the right professional is just a request away.
          </p>

          {/* Input */}
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-comp-2 w-full max-w-[750px] mt-4 mb-4">
            <div className="relative flex-1 group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
              <Input 
                value={needQuery}
                onChange={(e) => setNeedQuery(e.target.value)}
                placeholder="e.g. Find a maths tutor for Class 10..." 
                className="pl-12 h-14 text-body-large rounded-md bg-card border-border-interactive focus-visible:border-primary shadow-sm text-left"
              />
            </div>
            <ShinyButton 
              type="submit" 
              className="h-14 text-text-btn sm:w-auto w-full px-8"
              disabled={!needQuery.trim()}
            >
              Find Matches
              <ArrowRight className="w-4 h-4 ml-1" />
            </ShinyButton>
          </form>
          
        </section>

        {/* Suggestions Section */}
        <section className="py-section-2 flex flex-col items-center">
          <div className="flex flex-col w-full max-w-[750px] text-left">
            <span className="text-text-small text-muted-foreground font-medium tracking-widest uppercase mb-4 pl-3">
              TRY SOMETHING LIKE
            </span>
            <ul className="flex flex-col gap-1 w-full">
              {EXAMPLE_NEEDS.map((example, i) => (
                <li key={example} className="w-full">
                  <button
                    onClick={() => setNeedQuery(example)}
                    className="group w-full flex items-center gap-4 text-left p-3 rounded-md hover:bg-secondary transition-colors focus-ring"
                  >
                    <span className="text-primary font-mono text-sm opacity-60 group-hover:opacity-100 transition-opacity">
                      0{i + 1}
                    </span>
                    <span className="text-foreground font-medium group-hover:text-primary transition-colors">
                      {example}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Discovery Section */}
        <section className="py-section-2">
          <div className="flex items-end justify-between mb-section-1">
            <div>
              <h2 className="text-h1 font-bold text-foreground mb-2">Discover Categories</h2>
              <p className="text-body-large text-muted-foreground">Explore top-rated professionals in your area.</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-comp-3">
            {DISCOVERY_CATEGORIES.map((category) => (
              <div 
                key={category.id} 
                className="group relative bg-card border border-border rounded-md p-6 hover:border-primary transition-colors cursor-pointer focus-ring"
                tabIndex={0}
              >
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform origin-bottom-left">{category.icon}</div>
                <h3 className="text-h3 text-foreground mb-1">{category.title}</h3>
                <p className="text-text-small text-muted-foreground">{category.count}</p>
              </div>
            ))}
          </div>
        </section>

      </main>
    </div>
  );
}
