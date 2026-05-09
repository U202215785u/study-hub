import { Routes, Route } from 'react-router-dom';
import DietSchedule from './DietSchedule';

export default function DietPage() {
  return (
    <Routes>
      <Route path="/" element={<DietSchedule />} />
    </Routes>
  );
}
