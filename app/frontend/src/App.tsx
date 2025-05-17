import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { LandingPage, HomePage } from './components/Pages'
import routes from './config/routes'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path={routes.landing} element={<LandingPage />} />
        <Route path={routes.app} element={<HomePage />} />
        {/* Add more routes as needed */}
      </Routes>
    </Router>
  )
}

export default App
