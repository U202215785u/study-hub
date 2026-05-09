import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import TodayPage from '@/pages/Today/TodayPage';
import WorkoutPage from '@/pages/Workout/WorkoutPage';
import DietPage from '@/pages/Diet/DietPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import SettingsPage from '@/pages/Settings/SettingsPage';
import { seedDatabase } from '@/db/seed';

function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    seedDatabase().then(() => setReady(true));
  }, []);

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse-soft text-text-muted">加载中...</div>
      </div>
    );
  }

  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/today" replace />} />
          <Route path="today" element={<TodayPage />} />
          <Route path="workout/*" element={<WorkoutPage />} />
          <Route path="diet/*" element={<DietPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
