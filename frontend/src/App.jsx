import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Result from './pages/Result'
import History from './pages/History'
import Analytics from './pages/Analytics'
function App() {
  return (
    <BrowserRouter>
      <div className="flex">
        <Sidebar />

        <main className="flex-1 bg-gray-950 text-white p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/screening" element={<Screening />} />
            <Route path="/history" element={<History />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/result" element={<Result />} />
            
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App