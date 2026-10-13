import React from 'react';
import {createRoot} from 'react-dom/client';
import {MantineProvider,createTheme} from '@mantine/core';
import '@mantine/core/styles.css';
import '../../../web/src/style.css';
import {PublicPage} from '../../../web/src/PublicPage';
import {useHashRoute} from '../../../web/src/routes';
function App(){const route=useHashRoute();return <PublicPage route={route} staticDemo/>;}
createRoot(document.getElementById('root')!).render(<MantineProvider theme={createTheme({primaryColor:'cyan',fontFamily:'"Segoe UI", "Ubuntu", system-ui, sans-serif'})} forceColorScheme="dark"><App/></MantineProvider>);
