import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { SoundProvider } from './contexts/SoundContext'
import './index.css'
import '@fontsource/cinzel/index.css'; // Western Title Font
import '@fontsource/playfair-display/index.css'; // Western Body Font
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <SoundProvider>
        <App />
      </SoundProvider>
    </BrowserRouter>
  </StrictMode>,
)
