import { Routes, Route } from 'react-router-dom';
import WorkoutSchedule from './WorkoutSchedule';

export default function WorkoutPage() {
  return (
    <Routes>
      <Route path="/" element={<WorkoutSchedule />} />
    </Routes>
  );
}
