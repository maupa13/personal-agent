'use strict';

function patchEgressSystemView(){
  const system=$('#system');
  if(!system)return;
  try{
    const safe=JSON.parse(system.textContent||'{}');
    safe.egress_proxy=status?.egress_proxy||egressProxyStatus?.egress_proxy||null;
    system.textContent=JSON.stringify(safe,null,2);
  }catch(_){}
}

const __baseAdminLoad=load;
load=async function(){
  await __baseAdminLoad();
  try{
    const payload=await api('/api/admin/egress-proxy');
    egressProxyStatus=payload;
    if(status)status.egress_proxy=payload.egress_proxy||status.egress_proxy;
  }catch(_){}
  renderEgressProxySettings();
  patchEgressSystemView();
};

const __baseAdminRenderAll=renderAll;
renderAll=function(){
  __baseAdminRenderAll();
  renderEgressProxySettings();
  patchEgressSystemView();
};

const __baseAdminRenderSystem=renderSystem;
renderSystem=function(){
  __baseAdminRenderSystem();
  patchEgressSystemView();
};

(async()=>{
  for(let i=0;i<80;i++){
    if($('#admin')&&!$('#admin').hidden){
      try{
        const payload=await api('/api/admin/egress-proxy');
        egressProxyStatus=payload;
        if(status)status.egress_proxy=payload.egress_proxy||status.egress_proxy;
      }catch(_){}
      renderEgressProxySettings();
      patchEgressSystemView();
      break;
    }
    await new Promise(resolve=>setTimeout(resolve,100));
  }
})();
