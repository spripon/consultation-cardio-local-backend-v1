import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { purgeLegacyCloudKeys } from './lib/legacyCleanup'
import './index.css'

// Supprime toute clé d'API cloud héritée avant le premier rendu.
purgeLegacyCloudKeys();

createRoot(document.getElementById("root")!).render(<App />);
