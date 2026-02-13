import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { ConfigProvider } from 'antd'
import viVN from 'antd/locale/vi_VN'
import './styles/responsive.css'
import './styles/mobile-utils.css' 
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider
      locale={viVN}
      theme={{
        token: {
          colorPrimary: '#B01E23', 
          borderRadius: 6,
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        },
        components: {
          Layout: {
            headerBg: '#ffffff',
            bodyBg: '#f5f7fa', 
          },
          Card: {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)', 
          }
        }
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)