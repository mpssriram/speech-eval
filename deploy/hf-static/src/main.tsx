import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {MantineProvider,createTheme} from '@mantine/core';
import '@mantine/core/styles.css';
import '../../../web/src/style.css';
import {ExampleResults} from '../../../web/src/ExampleResults';
import examples from './catalog.js';
function App(){
 const [id,setId]=useState(examples.find(e=>e.default)?.id||examples[0].id),[error,setError]=useState('');
 return <div className="shell"><header className="app-header"><a className="brand" href="./">Speech-Eval</a><div className="header-picker"><label htmlFor="example">Recording / take</label><select id="example" value={id} onChange={e=>{setError('');setId(e.target.value);}}>{examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></div></header><main><div id="banner" className="banner">Precomputed demo. Live analysis of your own audio runs locally with Docker; see the GitHub README.</div>{error&&<p role="alert">{error}</p>}<ExampleResults id={id} onError={setError}/></main></div>;
}
createRoot(document.getElementById('root')!).render(<MantineProvider theme={createTheme({primaryColor:'cyan'})} forceColorScheme="dark"><App/></MantineProvider>);
