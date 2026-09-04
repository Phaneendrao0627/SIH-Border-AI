import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider, useTheme } from './context/ThemeContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Result from './pages/Result'
import History from './pages/History'
import Analytics from './pages/Analytics'

function MainLayout() {
  const { isDark } = useTheme()

  return (
    <div className={`flex min-h-screen transition-colors ${
      isDark ? 'bg-gray-950 text-white' : 'bg-slate-50 text-slate-900'
    }`}>
      <Sidebar />

      <main className="flex-1 p-8">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/screening" element={<Screening />} />
          <Route path="/history" element={<History />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/result" element={<Result />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <MainLayout />
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App