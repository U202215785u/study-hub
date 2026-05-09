import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { Home, Dumbbell, UtensilsCrossed, BarChart3, Settings } from 'lucide-react';

const tabs = [
  { path: '/today', label: '今日', icon: Home },
  { path: '/workout', label: '健身', icon: Dumbbell },
  { path: '/diet', label: '饮食', icon: UtensilsCrossed },
  { path: '/dashboard', label: '看板', icon: BarChart3 },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const startX = useRef(0);

  useEffect(() => {
    const idx = tabs.findIndex(t => location.pathname.startsWith(t.path));
    if (idx >= 0) setActiveTab(idx);
  }, [location]);

  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const diff = startX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0 && activeTab < tabs.length - 1) {
        navigate(tabs[activeTab + 1].path);
      } else if (diff < 0 && activeTab > 0) {
        navigate(tabs[activeTab - 1].path);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="bg-surface border-b border-border shrink-0 z-10">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-lg font-bold text-text">私人减肥教练</h1>
          <button
            onClick={() => navigate('/settings')}
            className="p-2 rounded-lg hover:bg-bg transition-colors"
          >
            <Settings size={20} className="text-text-muted" />
          </button>
        </div>
        {/* Tab Navigation */}
        <nav className="flex px-2 pb-2 gap-1">
          {tabs.map((tab, idx) => {
            const Icon = tab.icon;
            const isActive = activeTab === idx;
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-primary text-white'
                    : 'text-text-muted hover:bg-bg'
                }`}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </header>

      {/* Content */}
      <main
        ref={containerRef}
        className="flex-1 overflow-y-auto"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <div className="p-4 pb-24 animate-slide-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
