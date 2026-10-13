import {useEffect,useState} from 'react';
export function currentRoute():string {
 if(location.hash)return location.hash.slice(1)||'/';
 if(location.pathname.startsWith('/results/'))return '/analysis/'+location.pathname.split('/')[2];
 return '/';
}
export function useHashRoute(){
 const [route,setRoute]=useState(currentRoute);
 useEffect(()=>{const update=()=>setRoute(currentRoute());window.addEventListener('hashchange',update);window.addEventListener('popstate',update);return ()=>{window.removeEventListener('hashchange',update);window.removeEventListener('popstate',update);};},[]);
 return route;
}
export function navigate(path:string){location.hash=path;}
