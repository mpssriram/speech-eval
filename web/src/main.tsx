import React from 'react';
import { createRoot } from 'react-dom/client';
import {MantineProvider,createTheme} from '@mantine/core';
import '@mantine/core/styles.css';
import App from './App';
import './style.css';
const theme=createTheme({primaryColor:'cyan',fontFamily:'"Segoe UI", "Ubuntu", system-ui, sans-serif',defaultRadius:'md'});
createRoot(document.getElementById('root')!).render(<React.StrictMode><MantineProvider theme={theme} forceColorScheme="dark"><App/></MantineProvider></React.StrictMode>);
