import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import SecurityPortal from './pages/SecurityPortal'
import OperationsPortal from './pages/OperationsPortal'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/security" element={<SecurityPortal />} />
        <Route path="/operations" element={<OperationsPortal />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
