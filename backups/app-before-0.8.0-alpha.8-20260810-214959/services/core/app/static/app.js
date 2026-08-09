'use strict';

const UI_VERSION='0.8.0-alpha.8';
const STORAGE_KEY='par-conversations-v2';
const LEGACY_STORAGE_KEY='par-conversations-v1';
const ACTIVE_KEY='par-active-conversation';
const MODE_KEY='par-mode';
const PRESET_KEY='par-preset';
const LEGACY_CHAT='par-chat';
const MAX_CONVERSATIONS=100;
const MAX_MESSAGES=200;

const state={
  mode:localStorage.getItem(MODE_KEY)||'auto',
  preset:localStorage.getItem(PRESET_KEY)||'none',
  intentHint:'auto',
  auth:null,
  conversations:[],
  folders:[],
  activeFolderId:null,
  activeId:null,
  legacyConversations:[],
  system:null,
  search:'',
  searchMatches:null,
  busy:false,
  pendingFiles:[],
  artifacts:[],
  codeJobId:null,
  codePollTimer:null,
  taskMode:null,
  tasks:[],
  taskPollTimers:{},
  scenarios:[],
  scenarioId:null,
  webPreferences:null,
  experiencePreferences:null,
  connectionState:'booting',
  lastRuntimeError:null,
  animateMessageId:null,
};

const $=selector=>document.querySelector(selector);
const $$=selector=>Array.from(document.querySelectorAll(selector));
const chat=$('#chat');
const modes=$('#modes');
const input=$('#input');
const send=$('#send');
const conversationList=$('#conversations');

function uid(){
  if(globalThis.crypto?.randomUUID)return globalThis.crypto.randomUUID();
  return `c-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function now(){return Date.now()}
function current(){return state.conversations.find(c=>c.id===state.activeId)||null}
function cleanMessage(message){
  return {
    id:String(message?.id||uid()),
    role:message?.role==='assistant'?'assistant':'user',
    content:String(message?.content||'').slice(0,50000),
    kind:String(message?.kind||'message').slice(0,40),
    sources:Array.isArray(message?.sources)?message.sources.slice(0,12).map(source=>({title:String(source?.title||'').slice(0,300),url:String(source?.url||'').slice(0,2000),domain:String(source?.domain||'').slice(0,255),status:String(source?.status||'').slice(0,40),strategy:String(source?.strategy||'').slice(0,40),published_date:String(source?.published_date||'').slice(0,100),summary:String(source?.summary||'').slice(0,500),kind:String(source?.kind||'source').slice(0,40),price:String(source?.price||'').slice(0,64)})):[],
    attachments:Array.isArray(message?.attachments)?message.attachments.slice(0,12).map(item=>({artifact_id:String(item?.artifact_id||'').slice(0,64),name:String(item?.name||L('Файл','File')).slice(0,180),format:String(item?.format||'').slice(0,12),size:Number(item?.size)||0,download_url:String(item?.download_url||'').slice(0,400)})).filter(item=>item.artifact_id):[],
    metadata:(message?.metadata&&typeof message.metadata==='object')?JSON.parse(JSON.stringify(message.metadata)):{},
    createdAt:Number(message?.createdAt||message?.created_at)||now(),
  };
}
function normalizeConversation(conversation){
  return {
    id:String(conversation?.id||uid()),
    title:String(conversation?.title||defaultChatTitle()).replace(/\s+/g,' ').trim().slice(0,80)||defaultChatTitle(),
    messages:Array.isArray(conversation?.messages)?conversation.messages.slice(-MAX_MESSAGES).map(cleanMessage):[],
    updatedAt:Number(conversation?.updatedAt)||now(),
    customTitle:Boolean(conversation?.customTitle||conversation?.custom_title),
    folder_id:conversation?.folder_id||null,
    pinned_at:conversation?.pinned_at||null,
    archived_at:conversation?.archived_at||null,
    message_count:Number(conversation?.message_count)||0,
    preview:String(conversation?.preview||''),
  };
}
function titleFromMessages(messages){
  const first=(messages||[]).find(m=>m.role==='user'&&m.kind!=='capability-request'&&String(m.content||'').trim());
  if(!first)return defaultChatTitle();
  const text=String(first.content).replace(/\s+/g,' ').trim();
  return text.length>46?`${text.slice(0,46)}…`:text;
}
function loadJson(key,fallback){
  try{const parsed=JSON.parse(localStorage.getItem(key)||'');return parsed??fallback}catch(_){return fallback}
}
function loadStore(){
  let raw=loadJson(STORAGE_KEY,null);
  if(!Array.isArray(raw))raw=loadJson(LEGACY_STORAGE_KEY,[]);
  if(!Array.isArray(raw)){const legacy=loadJson(LEGACY_CHAT,[]);raw=Array.isArray(legacy)&&legacy.length?[{title:titleFromMessages(legacy),messages:legacy,updatedAt:now()}]:[]}
  state.legacyConversations=Array.isArray(raw)?raw.map(normalizeConversation):[];
  state.activeId=localStorage.getItem(ACTIVE_KEY)||null;
  state.activeFolderId=localStorage.getItem('par-active-folder')||null;
}
function saveStore(){
  state.conversations.sort((a,b)=>(b.updatedAt||b.updated_at||0)-(a.updatedAt||a.updated_at||0));
  if(state.activeId)localStorage.setItem(ACTIVE_KEY,state.activeId);else localStorage.removeItem(ACTIVE_KEY);
  if(state.activeFolderId)localStorage.setItem('par-active-folder',state.activeFolderId);else localStorage.removeItem('par-active-folder');
}
function serverConversation(raw){return normalizeConversation({id:raw.id,title:raw.title,messages:raw.messages||[],updatedAt:raw.updated_at||raw.updatedAt,customTitle:raw.custom_title||raw.customTitle,folder_id:raw.folder_id,pinned_at:raw.pinned_at,archived_at:raw.archived_at,message_count:raw.message_count,preview:raw.preview})}
async function loadServerStore(query=''){
  const params=new URLSearchParams({include_archived:'1'});if(query)params.set('q',query);
  let payload=await api(`/api/conversations?${params.toString()}`);
  if(!query&&!(payload.conversations||[]).length&&state.legacyConversations.length){
    try{await api('/api/conversations/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversations:state.legacyConversations})});localStorage.removeItem(STORAGE_KEY);localStorage.removeItem(LEGACY_STORAGE_KEY);localStorage.removeItem(LEGACY_CHAT);payload=await api('/api/conversations?include_archived=1')}catch(error){toast(`${L('Не удалось перенести старую историю','Could not migrate the previous history')}: ${error.message}`,'warning')}
  }
  state.folders=payload.folders||state.folders||[];
  if(query){state.searchMatches=new Set((payload.conversations||[]).map(item=>item.id));renderAll();return}
  state.searchMatches=null;state.conversations=(payload.conversations||[]).map(serverConversation);
  if(!state.conversations.length){const created=await api('/api/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:defaultChatTitle(),folder_id:state.activeFolderId||null})});state.conversations=[serverConversation(created.conversation)]}
  if(!state.conversations.some(c=>c.id===state.activeId))state.activeId=state.conversations[0]?.id||null;if(state.activeId)await loadConversation(state.activeId,false);
  saveStore();renderAll();
}
async function loadConversation(conversationId,render=true){
  const payload=await api(`/api/conversations/${encodeURIComponent(conversationId)}`);const full=serverConversation(payload.conversation);const index=state.conversations.findIndex(c=>c.id===conversationId);if(index>=0)state.conversations[index]=full;else state.conversations.unshift(full);state.activeId=conversationId;saveStore();if(render)renderAll();return full;
}
async function newConversation(render=true){
  const active=current();if(active&&active.messages?.length===0){state.activeId=active.id}else{const created=await api('/api/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:defaultChatTitle(),folder_id:state.activeFolderId||null})});state.conversations.unshift(serverConversation(created.conversation));state.activeId=created.conversation.id}
  saveStore();if(render){renderAll();input.focus();closeSidebar()}
}
async function selectConversation(conversationId){
  if(!state.conversations.some(c=>c.id===conversationId))return;await loadConversation(conversationId,true);closeSidebar();
}
async function deleteConversationNow(conversationId){
  await api(`/api/conversations/${encodeURIComponent(conversationId)}`,{method:'DELETE'});state.conversations=state.conversations.filter(c=>c.id!==conversationId);if(state.activeId===conversationId)state.activeId=state.conversations[0]?.id||null;if(!state.activeId)await newConversation(false);else await loadConversation(state.activeId,false);saveStore();renderAll();
}
async function clearCurrentNow(){
  const c=current();if(!c)return;const payload=await api(`/api/conversations/${c.id}/clear`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const full=serverConversation(payload.conversation);const index=state.conversations.findIndex(x=>x.id===c.id);if(index>=0)state.conversations[index]=full;renderAll();
}
async function clearAllNow(){
  const ids=state.conversations.map(c=>c.id);for(const id of ids){try{await api(`/api/conversations/${id}`,{method:'DELETE'})}catch(_){}}state.conversations=[];state.activeId=null;await newConversation(false);renderAll();
}
function prettySize(value){
  const bytes=Math.max(0,Number(value)||0);
  if(bytes<1024)return `${Math.round(bytes)} B`;
  const units=['KB','MB','GB','TB'];let amount=bytes/1024,unit=units[0];
  for(let i=1;i<units.length&&amount>=1024;i++){amount/=1024;unit=units[i]}
  const digits=amount>=100?0:(amount>=10?1:2);return `${amount.toFixed(digits)} ${unit}`;
}
function node(tag,className,text){
  const element=document.createElement(tag);
  if(className)element.className=className;
  if(text!==undefined)element.textContent=String(text);
  return element;
}
function relativeTime(timestamp){
  const delta=Math.max(0,Date.now()-Number(timestamp||0));
  if(delta<60000)return tr('now');
  if(delta<3600000)return `${Math.floor(delta/60000)} ${tr('minutes')}`;
  if(delta<86400000)return `${Math.floor(delta/3600000)} ${tr('hours')}`;
  return new Date(timestamp).toLocaleDateString(langKey()==='en'?'en-US':'ru-RU',{day:'2-digit',month:'short'});
}
function dateGroup(timestamp){const d=new Date(Number(timestamp||0));const nowD=new Date();const day=new Date(nowD.getFullYear(),nowD.getMonth(),nowD.getDate());const other=new Date(d.getFullYear(),d.getMonth(),d.getDate());const delta=Math.floor((day-other)/86400000);if(delta<=0)return tr('today');if(delta===1)return tr('yesterday');if(delta<7)return tr('last7');return tr('earlier')}
function renderFolders(){
  const host=$('#folders');if(!host)return;host.replaceChildren();
  const all=node('button',`folder-item${!state.activeFolderId?' active':''}`);all.type='button';all.append(node('span','folder-icon','▦'),node('span','folder-copy',tr('allChats')));all.onclick=()=>{state.activeFolderId=null;saveStore();renderAll()};host.append(all);
  for(const folder of state.folders){
    const row=node('div',`folder-item${state.activeFolderId===folder.id?' active':''}`);row.dataset.folderId=folder.id;
    const select=node('button','folder-select');select.type='button';const copy=node('span','folder-copy');copy.append(node('strong','',folder.name),node('small','',folder.conversation_count||0));select.append(node('span','folder-icon','▱'),copy);select.onclick=()=>{state.activeFolderId=folder.id;saveStore();renderAll()};
    const actions=node('span','folder-actions');const rename=node('button','folder-mini','✎');rename.type='button';rename.title=L('Переименовать проект','Rename project');rename.onclick=event=>{event.stopPropagation();renameFolder(folder)};const remove=node('button','folder-mini','×');remove.type='button';remove.title=L('Удалить проект','Delete project');remove.onclick=event=>{event.stopPropagation();deleteFolder(folder)};actions.append(rename,remove);row.append(select,actions);host.append(row);
  }
  const archivedCount=state.conversations.filter(c=>c.archived_at).length;const archive=node('button',`folder-item archive-item${state.activeFolderId==='__archived__'?' active':''}`);archive.type='button';archive.append(node('span','folder-icon','□'),node('span','folder-copy',`${tr('archive')}${archivedCount?` · ${archivedCount}`:''}`));archive.onclick=async()=>{state.activeFolderId='__archived__';const first=state.conversations.find(c=>c.archived_at);if(first)await loadConversation(first.id,false);saveStore();renderAll()};host.append(archive);
}
function renderConversations(){
  conversationList.replaceChildren();renderFolders();const visible=state.conversations.filter(c=>{const archive=Boolean(c.archived_at);const scope=state.activeFolderId==='__archived__'?archive:(!archive&&(!state.activeFolderId||c.folder_id===state.activeFolderId));return scope&&(!state.search||state.searchMatches?.has(c.id))});const groups=new Map();for(const c of visible){const key=dateGroup(c.updatedAt);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(c)}
  for(const [label,items] of groups){const section=node('div','conversation-group');section.append(node('div','conversation-group-title',label));for(const conversation of items){const row=node('div',`conversation-item${conversation.id===state.activeId?' active':''}`);row.dataset.id=conversation.id;row.setAttribute('role','button');row.tabIndex=0;row.onclick=()=>selectConversation(conversation.id);row.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectConversation(conversation.id)}};const icon=node('button','conversation-icon',conversation.pinned_at?'◆':'◌');icon.type='button';icon.title=conversation.pinned_at?L('Открепить','Unpin'):L('Закрепить','Pin');icon.onclick=async event=>{event.stopPropagation();await setConversationPinned(conversation,!conversation.pinned_at)};const copy=node('span','conversation-copy');copy.append(node('strong','',conversation.title),node('small','',relativeTime(conversation.updatedAt)));const remove=node('button','conversation-delete','×');remove.type='button';remove.title=L('Удалить диалог','Delete chat');remove.onclick=async event=>{event.stopPropagation();if(await confirmAction(L('Удалить диалог?','Delete chat?'),L(`«${conversation.title}» будет удалён из истории.`,`“${conversation.title}” will be removed from history.`),L('Удалить','Delete'),'danger')){try{await deleteConversationNow(conversation.id);toast(L('Диалог удалён','Chat deleted'),'success')}catch(error){toast(error.message,'warning')}}};row.append(icon,copy,remove);section.append(row)}conversationList.append(section)}
  $('#conversationEmpty').hidden=visible.length!==0;
}
function capChip(label,status){
  const element=node('span',`cap-chip ${status}`);
  element.append(node('span','cap-dot',''),node('span','',`${label}${status==='planned'?' · скоро':''}`));
  return element;
}
const WELCOME_PROMPTS={
 ru:[['preset','explain','Объяснить','Разобрать сложную тему простыми словами'],['preset','write','Написать','Подготовить текст, план или идею'],['preset','analyze','Проанализировать','Сравнить варианты и сделать вывод'],['intent','search','Найти','Найти актуальные данные и источники в интернете'],['intent','research','Исследовать','Собрать несколько источников, сравнить и сделать вывод']],
 en:[['preset','explain','Explain','Break down a complex topic in plain language'],['preset','write','Write','Prepare text, a plan or an idea'],['preset','analyze','Analyze','Compare options and make a conclusion'],['intent','search','Find','Find current information and sources on the web'],['intent','research','Research','Collect several sources, compare them and make a conclusion']]
};
const SCENARIO_I18N={clothing:['Choose clothes','Find items by size, budget, season and style','Help me choose clothes for my measurements and budget.'],procurement:['Find procurements','Find and filter suitable procurements and tenders','Find suitable procurements for my topic.'],real_estate:['Find property','Collect and compare suitable real-estate options','Help me find and compare suitable property options.'],gift:['Choose a gift','Find personalized gift ideas and buying options','Help me choose a good gift.'],product:['Choose a product','Compare products by real requirements and sources','Help me choose the best product for my needs.'],travel:['Plan a trip','Build an itinerary, options and practical trip details','Help me plan a trip.'],news:['Understand the news','Collect fresh sources and explain what happened','Collect fresh news on my topic and explain the key points.']};
function scenarioDisplay(item){if(langKey()!=='en')return item;const en=SCENARIO_I18N[item.id];return en?{...item,title:en[0],description:en[1],example_prompt:en[2]}:item}
function renderWelcome(){
  const wrap=node('div','welcome');
  wrap.append(node('div','welcome-mark','PA'),node('h1','',tr('welcomeTitle')),node('p','',tr('welcomeText')));
  const cards=node('div','starter-grid');
  const prompts=WELCOME_PROMPTS[langKey()];
  for(const [kind,id,title,description] of prompts){
    const active=kind==='preset'?state.preset===id:state.intentHint===id;
    const button=node('button',`starter-card${active?' active':''}`);button.type='button';button.dataset[kind==='preset'?'preset':'intent']=id;
    button.append(node('strong','',title),node('span','',description));
    button.onclick=()=>{state.scenarioId=null;if(kind==='preset'){state.intentHint='auto';state.preset=id;localStorage.setItem(PRESET_KEY,id);toast(`${L('Режим задачи','Task preset')}: ${title}`,'success')}else{state.preset='none';localStorage.setItem(PRESET_KEY,'none');state.intentHint=id;setBanner(id==='research'?L('Следующий запрос будет выполнен как исследование с несколькими веб-источниками.','The next request will run as research using multiple web sources.'):L('Следующий запрос будет выполнен с веб-поиском.','The next request will use web search.'),'info');toast(`${L('Веб-режим','Web mode')}: ${title}`,'success')}renderAll();input.focus()};
    cards.appendChild(button);
  }
  if(state.scenarios.length){
    wrap.append(node('h2','scenario-heading',tr('scenarioHeading')));
    const gallery=node('div','scenario-grid');
    for(const raw of state.scenarios.slice(0,8)){
      const item=scenarioDisplay(raw);const card=node('button',`scenario-card${state.scenarioId===item.id?' active':''}`);card.type='button';card.dataset.scenario=item.id;
      card.append(node('span','scenario-icon',item.icon||'◇'));const copy=node('span','scenario-copy');copy.append(node('strong','',item.title),node('small','',item.description));card.append(copy);
      card.onclick=()=>{state.scenarioId=item.id;state.preset='none';state.intentHint='auto';localStorage.setItem(PRESET_KEY,'none');input.value=item.example_prompt||'';resizeInput();renderAll();input.focus();input.setSelectionRange(input.value.length,input.value.length);toast(`${langKey()==='en'?'Assistant':'Помощник'}: ${item.title}`,'success')};gallery.append(card);
    }
    wrap.append(gallery);
  }
  const caps=node('div','capability-row');
  const capabilities=state.system?.capabilities||{chat:{status:'ready',label:'Чат'},web:{status:'planned',label:'Веб'},files:{status:'planned',label:'Файлы'}};
  const capLabels={chat:L('Чат','Chat'),web:L('Веб','Web'),research:L('Исследование','Research'),files:L('Файлы','Files'),code:L('Код','Code'),billing:L('Подписка','Subscription'),tasks:L('Задачи','Tasks'),deployment:L('Развёртывание','Deployment'),media:L('Медиа','Media')};for(const [key,capability] of Object.entries(capabilities).slice(0,4))caps.append(capChip(capLabels[key]||capability.label||L('Возможность','Capability'),capability.status||'planned'));
  wrap.append(cards,caps);
  chat.appendChild(wrap);
}

function appendInlineMarkdown(host,text){
  const pattern=/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\)|\*[^*\n]+\*)/g;
  let cursor=0;
  for(const match of text.matchAll(pattern)){
    if(match.index>cursor)host.append(document.createTextNode(text.slice(cursor,match.index)));
    const token=match[0];
    if(token.startsWith('**')){const strong=document.createElement('strong');strong.textContent=token.slice(2,-2);host.append(strong)}
    else if(token.startsWith('`')){const code=document.createElement('code');code.className='inline-code';code.textContent=token.slice(1,-1);host.append(code)}
    else if(token.startsWith('[')){
      const parts=token.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
      if(parts){const link=document.createElement('a');link.href=parts[2];link.target='_blank';link.rel='noopener noreferrer';link.textContent=parts[1];host.append(link)}
      else host.append(document.createTextNode(token));
    }else if(token.startsWith('*')){const em=document.createElement('em');em.textContent=token.slice(1,-1);host.append(em)}
    cursor=(match.index||0)+token.length;
  }
  if(cursor<text.length)host.append(document.createTextNode(text.slice(cursor)));
}
function renderTextBlock(host,text){
  const lines=text.replace(/\r/g,'').split('\n');
  let list=null;
  for(const raw of lines){
    const line=raw.trimEnd();
    if(!line.trim()){list=null;continue}
    const heading=line.match(/^(#{1,3})\s+(.+)$/);
    if(heading){list=null;const h=document.createElement(`h${Math.min(4,heading[1].length+2)}`);appendInlineMarkdown(h,heading[2]);host.append(h);continue}
    const bullet=line.match(/^[-*]\s+(.+)$/);
    if(bullet){if(!list||list.tagName!=='UL'){list=document.createElement('ul');host.append(list)}const li=document.createElement('li');appendInlineMarkdown(li,bullet[1]);list.append(li);continue}
    const ordered=line.match(/^\d+[.)]\s+(.+)$/);
    if(ordered){if(!list||list.tagName!=='OL'){list=document.createElement('ol');host.append(list)}const li=document.createElement('li');appendInlineMarkdown(li,ordered[1]);list.append(li);continue}
    list=null;
    if(line.startsWith('> ')){const quote=document.createElement('blockquote');appendInlineMarkdown(quote,line.slice(2));host.append(quote);continue}
    const paragraph=document.createElement('p');appendInlineMarkdown(paragraph,line);host.append(paragraph);
  }
}
function renderRichText(host,content){
  host.replaceChildren();
  const text=String(content||'');
  const fence=/```([^\n`]*)\n([\s\S]*?)```/g;
  let cursor=0;
  for(const match of text.matchAll(fence)){
    if((match.index||0)>cursor)renderTextBlock(host,text.slice(cursor,match.index));
    const block=node('div','code-block');
    const header=node('div','code-header');
    const language=(match[1]||'code').trim()||'code';
    const copy=node('button','code-copy',L('Копировать','Copy'));copy.type='button';
    const codeText=match[2].replace(/\n$/,'');
    copy.onclick=()=>copyText(codeText,copy);
    header.append(node('span','',language),copy);
    const pre=document.createElement('pre');const code=document.createElement('code');code.textContent=codeText;pre.appendChild(code);
    block.append(header,pre);host.append(block);
    cursor=(match.index||0)+match[0].length;
  }
  if(cursor<text.length)renderTextBlock(host,text.slice(cursor));
  if(!host.childNodes.length)host.textContent=text;
}
function sourceKindLabel(kind){
  const labels={news:["Новость","News"],product:["Товар","Product"],real_estate:["Объект","Property"],procurement:["Закупка","Procurement"],source:["Источник","Source"]};
  const pair=labels[kind]||labels.source;return L(pair[0],pair[1]);
}
function sourceHost(source){
  if(source.domain)return source.domain;
  try{return new URL(source.url).hostname.replace(/^www\./,'')}catch(_){return ''}
}
function sourceDate(value){
  if(!value)return '';
  const date=new Date(value);if(Number.isNaN(date.getTime()))return String(value).slice(0,32);
  return date.toLocaleString(langKey()==='en'?'en-US':'ru-RU',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
}
function renderSources(message){
  const sources=Array.isArray(message.sources)?message.sources.filter(source=>source&&source.url):[];if(!sources.length)return null;
  const kinds=new Set(sources.map(source=>source.kind||'source'));const mainKind=kinds.size===1?[...kinds][0]:'source';
  const wrap=node('section',`message-sources result-section kind-${mainKind}`);wrap.setAttribute('aria-label',L('Найденные материалы','Found results'));
  const heading=node('div','result-section-head');
  const title=node('div','sources-title',`${mainKind==='news'?L('Найденные новости','News found'):mainKind==='product'?L('Найденные варианты','Options found'):mainKind==='real_estate'?L('Найденные объекты','Properties found'):mainKind==='procurement'?L('Найденные закупки','Procurements found'):L('Источники','Sources')} · ${sources.length}`);
  heading.append(title);wrap.append(heading);
  const list=node('div','source-list result-card-grid');
  for(const [index,source] of sources.entries()){
    const kind=['news','product','real_estate','procurement'].includes(source.kind)?source.kind:'source';
    const link=node('a',`source-card result-card kind-${kind}`);link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';link.style.setProperty('--result-index',String(index));
    const top=node('div','result-card-top');const badge=node('span',`result-kind result-kind-${kind}`,sourceKindLabel(kind));const domain=node('span','result-domain',sourceHost(source));top.append(badge,domain);
    const label=node('strong','result-title',source.title||sourceHost(source)||source.url);link.append(top,label);
    if(source.summary){const summary=node('p','result-summary',source.summary);link.append(summary)}
    const meta=node('div','result-meta');const date=sourceDate(source.published_date);if(date)meta.append(node('span','result-date',date));if(source.price)meta.append(node('span','result-price',source.price));const method=source.strategy&&source.strategy!=='web'?source.strategy:'';if(method)meta.append(node('span','result-strategy',method));meta.append(node('span','result-open','↗'));link.append(meta);
    list.append(link)
  }
  wrap.append(list);return wrap
}
function renderMessageAttachments(message){
  const items=Array.isArray(message?.attachments)?message.attachments:[];if(!items.length)return null;
  const wrap=node('div','message-attachments');
  for(const item of items){const link=node('a','message-file');link.href=item.download_url||`/api/files/${item.artifact_id}/download`;link.target='_blank';link.rel='noopener';link.append(node('span','',String(item.format||'file').toUpperCase()),node('span','',item.name||L('Файл','File')));wrap.append(link)}
  return wrap;
}
function renderPendingFiles(){
  const bar=$('#attachmentBar');if(!bar)return;bar.replaceChildren();bar.hidden=state.pendingFiles.length===0;
  for(const item of state.pendingFiles){const chip=node('div','attachment-chip');chip.append(node('span','',String(item.format||'file').toUpperCase()));const copy=node('span','');copy.append(node('strong','',item.name),node('small','',prettySize(item.size)));const remove=node('button','','×');remove.type='button';remove.title=L('Убрать из следующего сообщения','Remove from the next message');remove.onclick=()=>{state.pendingFiles=state.pendingFiles.filter(x=>x.artifact_id!==item.artifact_id);renderPendingFiles()};chip.append(copy,remove);bar.append(chip)}
}
async function uploadSelectedFiles(files){
  for(const file of Array.from(files||[])){
    try{
      setBanner(`${L('Загружаю и проверяю','Uploading and verifying')} ${file.name}…`,'info');
      const response=await fetch('/api/files/upload',{method:'POST',headers:{'Content-Type':file.type||'application/octet-stream','X-PA-Filename':encodeURIComponent(file.name),...(state.auth?.csrf_token?{'X-CSRF-Token':state.auth.csrf_token}:{})},body:file});
      const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.error||L('Не удалось загрузить файл','Could not upload file'));
      state.pendingFiles.push(payload.artifact);state.pendingFiles=state.pendingFiles.slice(-12);renderPendingFiles();toast(`${file.name}: ${L('файл проверен','file verified')}`,'success');
    }catch(error){toast(`${file.name}: ${error.message}`,'error')}
  }
  setBanner(state.pendingFiles.length?L('Файлы прикреплены. Задайте вопрос или отправьте их для анализа.','Files attached. Ask a question or send them for analysis.'):'');
  await loadArtifacts();
}
function openFilePicker(){$('#fileInput')?.click()}
function renderArtifactList(){
  const host=$('#artifactList');if(!host)return;host.replaceChildren();
  if(!state.artifacts.length){host.append(node('div','muted',L('В workspace пока нет файлов.','There are no files in the workspace yet.')));return}
  for(const item of state.artifacts){
    const row=node('div','artifact-row');row.dataset.artifactId=item.artifact_id;row.append(node('div','artifact-kind',String(item.format||'file').toUpperCase()));
    const copy=node('div','artifact-copy');copy.append(node('strong','',item.name),node('small','',`v${item.version} · ${prettySize(item.size)} · ${item.validation_status}`));
    const actions=node('div','artifact-actions');const attach=node('button','',L('В чат','Attach'));attach.type='button';attach.onclick=()=>{if(!state.pendingFiles.some(x=>x.artifact_id===item.artifact_id))state.pendingFiles.push(item);renderPendingFiles();closeSettings();input.focus();toast(L('Файл прикреплён','File attached'),'success')};
    const download=node('a','',L('Скачать','Download'));download.href=item.download_url;download.target='_blank';download.rel='noopener';
    const remove=node('button','',L('Удалить','Delete'));remove.type='button';remove.onclick=async()=>{if(!await confirmAction(L('Удалить файл?','Delete file?'),L(`«${item.name}» будет удалён из workspace.`,`“${item.name}” will be deleted from the workspace.`),L('Удалить','Delete'),'danger'))return;try{await api(`/api/files/${item.artifact_id}`,{method:'DELETE'});state.pendingFiles=state.pendingFiles.filter(x=>x.artifact_id!==item.artifact_id);renderPendingFiles();await loadArtifacts();toast(L('Файл удалён','File deleted'),'success')}catch(error){toast(error.message,'error')}};
    actions.append(attach,download,remove);row.append(copy,actions);host.append(row);
  }
}
async function loadArtifacts(){try{const result=await api('/api/files');state.artifacts=result.artifacts||[];renderArtifactList()}catch(error){state.artifacts=[];renderArtifactList();if(state.system?.debug_diagnostics||state.auth?.user?.role==='OWNER'||state.auth?.user?.role==='ADMIN')console.error('artifact.list.failed',{message:error?.message||String(error),request_id:error?.request_id||'',correlation_id:error?.correlation_id||'',duration_ms:error?.duration_ms||0});}}
async function createArtifactFromUi(){
  const fmt=$('#artifactFormat').value;let name=$('#artifactName').value.trim()||`document.${fmt}`;if(!name.toLowerCase().endsWith(`.${fmt}`))name=`${name.replace(/\.[^.]+$/,'')}.${fmt}`;
  let content=$('#artifactContent').value;if(fmt==='json'){try{content=JSON.parse(content)}catch(_){toast(L('Для JSON введите корректный JSON','Enter valid JSON'),'error');return}}
  if(fmt==='csv'){content={rows:content.split(/\r?\n/).filter(Boolean).map(line=>line.split(',').map(cell=>cell.trim()))}}
  try{const result=await api('/api/files/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({format:fmt,name,content})});state.pendingFiles.push(result.artifact);renderPendingFiles();await loadArtifacts();toast(`${result.artifact.name}: ${L('создан и проверен','created and verified')}`,'success')}catch(error){toast(error.message,'error')}
}

function formatDuration(ms){const value=Number(ms||0);if(!Number.isFinite(value)||value<0)return '';if(value<1000)return `${Math.round(value)} ms`;return `${(value/1000).toFixed(value<10000?1:0)} s`}
function renderQuickReplies(message){
  const options=Array.isArray(message?.metadata?.quick_replies)?message.metadata.quick_replies.filter(Boolean).slice(0,12):[];if(!options.length)return null;
  const wrap=node('div','quick-replies');for(const option of options){const button=node('button','quick-reply',String(option));button.type='button';button.onclick=()=>{input.value=String(option);resizeInput();input.focus();sendRequest({addUser:true})};wrap.append(button)}return wrap;
}
function renderMessageMeta(message){
  if(message.role!=='assistant'||!message.metadata||typeof message.metadata!=='object')return null;
  const meta=message.metadata;const duration=formatDuration(meta.duration_ms);if(!duration&&!meta.debug)return null;
  const wrap=node('div','message-meta');if(duration)wrap.append(node('span','message-meta-chip',`⏱ ${duration}`));
  if(Number(meta.source_count)>0)wrap.append(node('span','message-meta-chip',`${L('источников','sources')}: ${Number(meta.source_count)}`));
  if(meta.debug&&typeof meta.debug==='object'){const details=document.createElement('details');details.className='message-debug';const summary=node('summary','',L('Диагностика','Diagnostics'));details.append(summary);const native=meta.inference_native||{};const rows=[['request',meta.request_id],['correlation',meta.correlation_id],['intent',meta.intent],['routing',formatDuration(meta.routing_ms)],['web',formatDuration(meta.web_ms)],['inference',formatDuration(meta.inference_ms)],['model load',formatDuration(native.load_ms)],['prompt eval',formatDuration(native.prompt_eval_ms)],['generation',formatDuration(native.generation_ms)],['output tokens',native.output_tokens],['tokens/sec',native.tokens_per_sec],['target',meta.debug.execution_target],['execution',meta.debug.execution_policy]];for(const [key,value] of rows){if(value!==undefined&&value!==null&&String(value)!=='')details.append(node('div','message-debug-row',`${key}: ${value}`))}wrap.append(details)}
  return wrap
}

function renderMessageActions(message,index){
  const actions=node('div','message-actions');
  const copy=node('button','message-action',L('Копировать','Copy'));copy.type='button';copy.onclick=()=>copyText(message.content,copy);actions.append(copy);
  if(message.role==='assistant'&&message.kind!=='capability'){
    const regenerate=node('button','message-action',L('Повторить','Retry'));regenerate.type='button';regenerate.onclick=()=>regenerateAt(index);actions.append(regenerate);
  }
  return actions;
}
function progressiveReveal(bubble,message){
  const text=String(message.content||'');const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce||text.length<90){renderRichText(bubble,text);state.animateMessageId=null;return}
  bubble.replaceChildren();bubble.classList.add('progressive-reveal');bubble.setAttribute('aria-busy','true');
  const started=performance.now();const targetMs=Math.max(500,Math.min(1800,text.length*2.1));let last=-1;
  function tick(ts){if(!bubble.isConnected||state.animateMessageId!==message.id)return;const progress=Math.min(1,(ts-started)/targetMs);const eased=1-Math.pow(1-progress,2.2);let pos=Math.max(last+1,Math.floor(text.length*eased));if(pos<text.length){const next=text.indexOf(' ',pos);if(next>pos&&next-pos<18)pos=next}pos=Math.min(text.length,pos);if(pos!==last){bubble.textContent=text.slice(0,pos);last=pos;if(pos%180<24)document.scrollingElement?.scrollTo({top:document.scrollingElement.scrollHeight,behavior:'instant'})}if(progress<1)requestAnimationFrame(tick);else{bubble.classList.remove('progressive-reveal');bubble.removeAttribute('aria-busy');renderRichText(bubble,text);state.animateMessageId=null}}
  requestAnimationFrame(tick);
}
function renderChat(){
  chat.replaceChildren();
  const conversation=current();
  $('#conversationTitle').textContent=conversation?.title||defaultChatTitle();
  if(!conversation||conversation.messages.length===0){renderWelcome();return}
  conversation.messages.forEach((message,index)=>{
    const row=node('article',`message-row ${message.role}${message.kind==='capability'?' capability-message':''}`);
    row.dataset.messageId=message.id;
    const avatar=node('div','avatar',message.role==='user'?'':'PA');
    const body=node('div','message-body');
    if(message.role!=='user')body.append(node('div','message-author',tr('brand')));
    const bubble=node('div',`msg ${message.role}`);
    if(message.role==='assistant'&&state.animateMessageId===message.id)progressiveReveal(bubble,message);else if(message.role==='assistant')renderRichText(bubble,message.content);else bubble.textContent=message.content;
    body.append(bubble);const quickReplies=renderQuickReplies(message);if(quickReplies)body.append(quickReplies);const attachments=renderMessageAttachments(message);if(attachments)body.append(attachments);const sources=renderSources(message);if(sources)body.append(sources);const meta=renderMessageMeta(message);if(meta)body.append(meta);body.append(renderMessageActions(message,index));
    row.append(avatar,body);chat.appendChild(row);
  });
  requestAnimationFrame(()=>{document.scrollingElement?.scrollTo({top:document.scrollingElement.scrollHeight,behavior:'instant'})});
}
function entitlementEnabled(key){const item=state.auth?.entitlements?.features?.[key];return item?!!item.enabled:true}
function renderModes(){
  modes.replaceChildren();let defs=state.system?.modes||[];defs=defs.filter(mode=>entitlementEnabled(`mode_${mode.id}`));if(!defs.length)defs=(state.system?.modes||[]).filter(mode=>mode.id==='auto');
  if(!defs.some(item=>item.id===state.mode)){state.mode=defs[0]?.id||'auto';localStorage.setItem(MODE_KEY,state.mode)}
  const currentMode=defs.find(item=>item.id===state.mode)||defs[0];if(currentMode)$('#modeButton').firstChild.textContent=`${currentMode.label||currentMode.id} `;
  for(const mode of defs){const button=node('button',`mode${mode.id===state.mode?' active':''}`,mode.label||mode.id);button.type='button';button.dataset.mode=mode.id;button.title=mode.description||'';button.onclick=()=>{state.mode=mode.id;localStorage.setItem(MODE_KEY,mode.id);modes.hidden=true;$('#modeButton').setAttribute('aria-expanded','false');renderModes();toast(`${L('Режим','Mode')}: ${mode.label||mode.id}`)};modes.appendChild(button)}
}
function renderToneMenu(){const host=$('#toneMenu');if(!host)return;host.replaceChildren();const defs=state.system?.tones||[];const current=state.experiencePreferences?.tone||'normal';const labels=langKey()==='en'?{normal:'Normal',friendly:'Friendly',ironic:'Ironic',meme:'Meme',serious:'Very serious',expert:'Expert',brief:'Brief',detailed:'Detailed'}:{normal:'Обычный',friendly:'Дружелюбный',ironic:'С иронией',meme:'Мемный',serious:'Очень серьёзный',expert:'Экспертный',brief:'Кратко',detailed:'Подробно'};const button=$('#toneButton');if(button){button.textContent=current==='normal'?'✨':`${current==='meme'?'😂':current==='ironic'?'😏':current==='serious'?'🧐':current==='expert'?'🎓':current==='brief'?'⚡':current==='detailed'?'📚':'✨'}`;button.title=`${langKey()==='en'?'Style':'Стиль'}: ${labels[current]||current}`}for(const tone of defs){const item=node('button',`mode${tone.id===current?' active':''}`,labels[tone.id]||tone.label||tone.id);item.type='button';item.onclick=async()=>{try{const payload=await api('/api/preferences/experience',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tone:tone.id})});state.experiencePreferences=payload.preferences;renderExperiencePreferences();host.hidden=true;$('#toneButton').setAttribute('aria-expanded','false');toast(`${langKey()==='en'?'Style':'Стиль'}: ${labels[tone.id]||tone.id}`,'success')}catch(error){toast(friendlyError(error).title,'error')}};host.append(item)}}
function renderCapabilities(){
  const host=$('#capabilitySettings');if(!host)return;host.replaceChildren();
  for(const [key,capability] of Object.entries(state.system?.capabilities||{})){
    const row=node('div','capability-setting');const feature=key==='files'?'files_read':key;const entitled=entitlementEnabled(feature);
    const copy=node('div','');copy.append(node('strong','',capability.label||key),node('span','',!entitled?L('Недоступно на текущем тарифе','Unavailable on the current plan'):capability.status==='ready'?L('Доступно в текущей сборке','Available in this build'):L('Подключается отдельным продуктовым слоем','Coming in a separate product layer')));
    const badgeText=!entitled?L('Тариф','Plan'):capability.status==='ready'?L('Готово','Ready'):L('Запланировано','Planned');row.append(copy,node('span',`capability-badge ${!entitled?'locked':capability.status||'planned'}`,badgeText));host.append(row);
  }
}
function renderAll(){renderConversations();renderChat();renderModes();renderCapabilities();renderPendingFiles();renderArtifactList()}
function addMessage(message){
  const conversation=current();if(!conversation)return null;
  const clean=cleanMessage(message);conversation.messages.push(clean);conversation.messages=conversation.messages.slice(-MAX_MESSAGES);if(!conversation.customTitle)conversation.title=titleFromMessages(conversation.messages);conversation.updatedAt=now();saveStore();renderAll();return clean;
}
function setBanner(text,type='info'){
  const banner=$('#capabilityBanner');
  if(!text){banner.hidden=true;banner.textContent='';return}
  banner.hidden=false;banner.className=`capability-banner ${type}`;banner.textContent=text;
}
function setBusy(busy){
  state.busy=busy;send.disabled=busy;input.disabled=busy;chat.setAttribute('aria-busy',String(busy));send.classList.toggle('working',busy);send.querySelector('span:first-child').textContent=busy?tr('thinking'):tr('send');
}
function setThinking(show){
  $('#thinkingRow')?.remove();
  if(!show)return;
  const row=node('article','message-row assistant thinking-row');row.id='thinkingRow';
  const avatar=node('div','avatar','PA');const body=node('div','message-body');body.append(node('div','message-author',tr('brand')));
  const dots=node('div','thinking-dots');dots.append(node('span'),node('span'),node('span'));body.append(dots);row.append(avatar,body);chat.append(row);requestAnimationFrame(()=>row.scrollIntoView({block:'end'}));
}

async function api(path,options){
  const opts={...(options||{})};const method=String(opts.method||'GET').toUpperCase();opts.headers={...(opts.headers||{})};
  if(!['GET','HEAD','OPTIONS'].includes(method)&&state.auth?.csrf_token)opts.headers['X-CSRF-Token']=state.auth.csrf_token;
  let response;try{response=await fetch(path,opts)}catch(cause){const error=new Error('network unavailable');error.status=0;error.code='network_unavailable';error.cause=cause;throw error}
  let payload={};try{payload=await response.json()}catch(_){}
  if(!response.ok){const error=new Error(payload.error||'request failed');error.status=response.status;error.code=payload.code;error.capability=payload.capability;error.request_id=payload.request_id||response.headers.get('X-Request-ID')||'';error.correlation_id=payload.correlation_id||response.headers.get('X-Correlation-ID')||'';error.duration_ms=payload.duration_ms??Number(response.headers.get('X-PA-Duration-Ms')||0);error.debug=payload.debug||null;throw error}
  return payload;
}
function friendlyError(error){const status=Number(error?.status||0),code=String(error?.code||'');if(status===0||code==='network_unavailable')return{kind:'offline',title:tr('runtimeOfflineTitle'),detail:tr('runtimeOfflineDetail')};if(status===429||code.includes('quota'))return{kind:'quota',title:tr('runtimeQuotaTitle'),detail:tr('runtimeQuotaDetail')};if(status===401)return{kind:'permission',title:langKey()==='en'?'Sign in required':'Нужно войти',detail:langKey()==='en'?'Your session is not active. Sign in and retry.':'Сессия не активна. Войдите в аккаунт и повторите.'};if(status===403)return{kind:'permission',title:tr('runtimePermissionTitle'),detail:tr('runtimePermissionDetail')};if(status===503||status===502||status===504)return{kind:'degraded',title:tr('runtimeDegradedTitle'),detail:tr('runtimeDegradedDetail')};return{kind:'error',title:tr('runtimeErrorTitle'),detail:tr('runtimeErrorDetail')}}
function showRuntimeState(kind,title,detail,{retry=true}={}){state.connectionState=kind;const host=$('#runtimeStateBanner');if(!host)return;if(kind==='ready'){host.hidden=true;host.className='runtime-state';return}host.hidden=false;host.className=`runtime-state ${kind}`;setText('#runtimeStateTitle',title||'');setText('#runtimeStateDetail',detail||'');$('#runtimeRetry').hidden=!retry;const icons={booting:'◌',starting:'◌',degraded:'△',offline:'×',quota:'!',permission:'!',error:'!'};setText('#runtimeStateIcon',icons[kind]||'!')}
function updateRuntimeStateCopy(){const kind=state.connectionState;if(kind==='ready')return showRuntimeState('ready','','');if(kind==='booting'||kind==='starting')showRuntimeState(kind,tr('runtimeStartingTitle'),tr('runtimeStartingDetail'));else if(kind==='offline')showRuntimeState(kind,tr('runtimeOfflineTitle'),tr('runtimeOfflineDetail'));else if(kind==='quota')showRuntimeState(kind,tr('runtimeQuotaTitle'),tr('runtimeQuotaDetail'));else if(kind==='permission')showRuntimeState(kind,tr('runtimePermissionTitle'),tr('runtimePermissionDetail'));else if(kind==='degraded')showRuntimeState(kind,tr('runtimeDegradedTitle'),tr('runtimeDegradedDetail'));else if(kind==='error')showRuntimeState(kind,tr('runtimeErrorTitle'),tr('runtimeErrorDetail'))}

function semanticVersion(value){const match=String(value||'').match(/\d+\.\d+\.\d+/);return match?match[0]:null}
function enforceUiVersion(systemVersion){
  const backend=semanticVersion(systemVersion);const ui=semanticVersion(document.querySelector('meta[name="app-version"]')?.content||UI_VERSION);
  if(!backend||!ui||backend===ui)return true;
  const key=`par-ui-reloaded-${backend}`;
  if(sessionStorage.getItem(key)!=='1'){
    sessionStorage.setItem(key,'1');
    const url=new URL(location.href);url.searchParams.set('ui',backend);location.replace(url.toString());return false;
  }
  setBanner(L(`Интерфейс ${ui} не совпадает с Core ${backend}. Выполните REPAIR и обновите страницу.`,`UI ${ui} does not match Core ${backend}. Run REPAIR and refresh the page.`),'warning');return true;
}
const I18N={
 ru:{brand:'Родной Агент',edition:'Локальная версия',pageTitle:'Родной Агент',newChat:'Новый чат',newProject:'Новый проект',search:'Поиск диалогов',projects:'Проекты',dialogs:'Диалоги',clear:'Очистить',files:'Файлы',code:'Код',tasks:'Задачи',settings:'Настройки',profile:'Профиль',help:'Помощь',feedback:'Обратная связь',admin:'Администрирование',send:'Отправить',thinking:'Думаю…',placeholder:'Напишите сообщение…',share:'Поделиться',download:'Скачать',ready:'Готов',starting:'Запускается',offline:'Нет связи',retry:'Повторить',allChats:'Все чаты',archive:'Архив',now:'сейчас',minutes:'мин',hours:'ч',today:'Сегодня',yesterday:'Вчера',last7:'Последние 7 дней',earlier:'Ранее',nothingFound:'Ничего не найдено',welcomeTitle:'Чем займёмся?',welcomeText:'Родной Агент помогает решать задачи с интернетом, файлами, кодом и проверяемыми результатами. Технические детали остаются в администрировании.',scenarioHeading:'Попробуйте решить задачу',localStatus:'Локальный режим',topbarSubtitle:'Помощник, который делает работу вместе с вами',runtimeOfflineTitle:'Связь с агентом потеряна',runtimeOfflineDetail:'Ваши данные сохранены. Проверьте, что Personal Agent запущен, и повторите подключение.',runtimeStartingTitle:'Система запускается',runtimeStartingDetail:'Некоторые возможности ещё готовятся. Чат станет доступен сразу после проверки runtime.',runtimeDegradedTitle:'Часть возможностей ограничена',runtimeDegradedDetail:'Основной интерфейс доступен. Недоступный модуль можно проверить в настройках или диагностике.',runtimeQuotaTitle:'Достигнут лимит тарифа',runtimeQuotaDetail:'Данные не потеряны. Измените режим выполнения, дождитесь обновления лимита или выберите другой тариф.',runtimePermissionTitle:'Недостаточно прав',runtimePermissionDetail:'Эта операция недоступна вашей роли или текущему тарифу.',runtimeErrorTitle:'Не удалось выполнить запрос',runtimeErrorDetail:'Данные сохранены. Можно повторить после восстановления сервиса.',general:'Общие',data:'Данные',webSites:'Веб и сайты',capabilities:'Возможности',interfaceStyle:'Интерфейс и стиль',uiLanguage:'Язык интерфейса',responseLanguage:'Язык ответов',theme:'Тема',uiScale:'Масштаб интерфейса',scaleCompact:'Компактный',scaleNormal:'Обычный',scaleLarge:'Крупный',execution:'Где выполнять',tone:'Стиль ответа',save:'Сохранить',saved:'Сохранено',systemTheme:'Как в системе',dark:'Тёмная',light:'Светлая',answerLikeQuery:'Как в запросе',auto:'Авто',localOnly:'Только локально',preferLocal:'Предпочитать локально',remoteAllowed:'Можно удалённо',remoteOnly:'Только удалённо',toneNormal:'Обычный',toneFriendly:'Дружелюбный',toneIronic:'С иронией',toneMeme:'Мемный',toneSerious:'Очень серьёзный',toneExpert:'Экспертный',toneBrief:'Кратко',toneDetailed:'Подробно',settingsTitle:'Настройки',historyData:'История и данные',internetSearch:'Поиск в интернете',workspaceArtifacts:'Workspace и артефакты',safeCode:'Код и безопасный запуск',tasksProgress:'Задачи и прогресс',helpTitle:'Помощь и возможности',tourBack:'Назад',tourNext:'Далее',tourDone:'Готово',tourSkip:'Пропустить'},
 en:{brand:'Personal Agent',edition:'Local edition',pageTitle:'Personal Agent',newChat:'New chat',newProject:'New project',search:'Search chats',projects:'Projects',dialogs:'Chats',clear:'Clear',files:'Files',code:'Code',tasks:'Tasks',settings:'Settings',profile:'Profile',help:'Help',feedback:'Feedback',admin:'Administration',send:'Send',thinking:'Thinking…',placeholder:'Write a message…',share:'Share',download:'Download',ready:'Ready',starting:'Starting',offline:'Offline',retry:'Retry',allChats:'All chats',archive:'Archive',now:'now',minutes:'min',hours:'h',today:'Today',yesterday:'Yesterday',last7:'Last 7 days',earlier:'Earlier',nothingFound:'Nothing found',welcomeTitle:'What shall we do?',welcomeText:'Personal Agent helps with web research, files, code and verified results. Technical details stay in Administration.',scenarioHeading:'Try a real task',localStatus:'Local mode',topbarSubtitle:'An assistant that works on the task with you',runtimeOfflineTitle:'Connection to Personal Agent was lost',runtimeOfflineDetail:'Your data is safe. Make sure Personal Agent is running and retry the connection.',runtimeStartingTitle:'System is starting',runtimeStartingDetail:'Some capabilities are still warming up. Chat will be available after runtime checks complete.',runtimeDegradedTitle:'Some capabilities are limited',runtimeDegradedDetail:'The main interface is available. Check the affected module in Settings or Diagnostics.',runtimeQuotaTitle:'Plan limit reached',runtimeQuotaDetail:'No data was lost. Change execution mode, wait for the limit to renew, or choose another plan.',runtimePermissionTitle:'Permission required',runtimePermissionDetail:'This action is unavailable for your role or current plan.',runtimeErrorTitle:'The request could not be completed',runtimeErrorDetail:'Your data is safe. You can retry after the service recovers.',general:'General',data:'Data',webSites:'Web & sites',capabilities:'Capabilities',interfaceStyle:'Interface & style',uiLanguage:'Interface language',responseLanguage:'Response language',theme:'Theme',uiScale:'Interface scale',scaleCompact:'Compact',scaleNormal:'Normal',scaleLarge:'Large',execution:'Execution',tone:'Response style',save:'Save',saved:'Saved',systemTheme:'System',dark:'Dark',light:'Light',answerLikeQuery:'Match the request',auto:'Auto',localOnly:'Local only',preferLocal:'Prefer local',remoteAllowed:'Remote allowed',remoteOnly:'Remote only',toneNormal:'Normal',toneFriendly:'Friendly',toneIronic:'Ironic',toneMeme:'Meme',toneSerious:'Very serious',toneExpert:'Expert',toneBrief:'Brief',toneDetailed:'Detailed',settingsTitle:'Settings',historyData:'History & data',internetSearch:'Web search',workspaceArtifacts:'Workspace & artifacts',safeCode:'Code & safe execution',tasksProgress:'Tasks & progress',helpTitle:'Help & capabilities',tourBack:'Back',tourNext:'Next',tourDone:'Done',tourSkip:'Skip'}
};
function langKey(){return state.experiencePreferences?.ui_language==='en'?'en':'ru'}
function tr(key){const lang=langKey();return I18N[lang][key]??I18N.ru[key]??key}
function L(ru,en){return langKey()==='en'?en:ru}
function defaultChatTitle(){return L('Новый чат','New chat')}
function effectiveTheme(value){if(value==='light'||value==='dark')return value;return matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}
function applyTheme(value){const theme=effectiveTheme(value||state.experiencePreferences?.theme||'system');document.documentElement.dataset.theme=theme;localStorage.setItem('par-theme-preference',value||'system');document.querySelector('meta[name="theme-color"]')?.setAttribute('content',theme==='light'?'#f6f7f9':'#0b0c0f')}
function applyUiScale(value){const scale=['compact','normal','large'].includes(value)?value:'normal';document.documentElement.dataset.uiScale=scale;localStorage.setItem('par-ui-scale',scale)}
function executionLabel(value){const key={auto:'auto',local_only:'localOnly',prefer_local:'preferLocal',remote_allowed:'remoteAllowed',remote_only:'remoteOnly'}[value]||'auto';return tr(key)}
function setText(selector,value){const element=$(selector);if(element)element.textContent=value}
function setLabelText(controlId,value){const control=$(controlId);const label=control?.closest('label');if(!label)return;for(const child of label.childNodes){if(child.nodeType===Node.TEXT_NODE&&child.textContent.trim()){child.textContent=value;break}}}
function setOptionText(selectId,value,text){const option=$(`${selectId} option[value="${value}"]`);if(option)option.textContent=text}
function applyLanguage(lang){
  lang=lang==='en'?'en':'ru';if(!state.experiencePreferences)state.experiencePreferences={};state.experiencePreferences.ui_language=lang;localStorage.setItem('par-ui-language',lang);document.documentElement.lang=lang;const t=I18N[lang];document.title=t.pageTitle;
  setText('#brandName',t.brand);setText('#brandEdition',t.edition);setText('#versionBrand',t.brand);setText('#topbarSubtitle',t.topbarSubtitle);setText('#newChat span:nth-child(2)',t.newChat);setText('#newFolder .new-project-label',t.newProject);if($('#chatSearch')){$('#chatSearch').placeholder=t.search;$('#chatSearch').setAttribute('aria-label',t.search)}setText('.project-heading .sidebar-section-title',t.projects);const titles=$$('.sidebar-section-row .sidebar-section-title');if(titles[1])titles[1].textContent=t.dialogs;setText('#clearAllShortcut',t.clear);setText('#conversationEmpty',t.nothingFound);setText('#filesEntry span:nth-child(2)',t.files);setText('#codeEntry span:nth-child(2)',t.code);setText('#tasksEntry span:nth-child(2)',t.tasks);setText('#settingsEntry span:nth-child(2)',t.settings);setText('#helpEntry span:nth-child(2)',t.help);setText('#feedbackEntry span:nth-child(2)',t.feedback);setText('#adminEntry span:nth-child(2)',t.admin);if(input)input.placeholder=t.placeholder;setText('#send span:first-child',state.busy?t.thinking:t.send);setText('#shareChatButton span:last-child',t.share);setText('#exportChatButton span:last-child',t.download);setText('#sideHealth',state.connectionState==='ready'?t.ready:$('#sideHealth')?.textContent||t.starting);
  setText('#settingsEyebrow',lang==='en'?'PERSONAL AGENT':'Родной Агент');setText('#helpEyebrow',lang==='en'?'PERSONAL AGENT':'Родной Агент');setText('#settingsTitle',t.settingsTitle);setText('#helpTitle',t.helpTitle);
  const tabs={general:t.general,data:t.data,web:t.webSites,files:t.files,code:t.code,tasks:t.tasks,capabilities:t.capabilities};for(const [id,label] of Object.entries(tabs))setText(`[data-settings-tab="${id}"]`,label);
  setText('[data-settings-panel="general"] h3',t.interfaceStyle);setText('[data-settings-panel="data"] h3',t.historyData);setText('[data-settings-panel="web"] h3',t.internetSearch);setText('[data-settings-panel="files"] h3',t.workspaceArtifacts);setText('[data-settings-panel="code"] h3',t.safeCode);setText('[data-settings-panel="tasks"] h3',t.tasksProgress);setText('[data-settings-panel="capabilities"] h3',t.capabilities);
  setLabelText('#uiLanguage',t.uiLanguage);setLabelText('#responseLanguage',t.responseLanguage);setLabelText('#themeSelect',t.theme);setLabelText('#uiScale',t.uiScale);if($('#webNewsInterestsLabel'))$('#webNewsInterestsLabel').childNodes[0].nodeValue=(langKey()==='en'?'News topics I care about ':'Темы новостей, которые мне интересны ');setLabelText('#executionPolicy',t.execution);setLabelText('#tonePreset',t.tone);setText('#saveExperiencePreferences',t.save);
  setOptionText('#responseLanguage','auto',t.answerLikeQuery);setOptionText('#themeSelect','system',t.systemTheme);setOptionText('#themeSelect','dark',t.dark);setOptionText('#themeSelect','light',t.light);setOptionText('#uiScale','compact',t.scaleCompact);setOptionText('#uiScale','normal',t.scaleNormal);setOptionText('#uiScale','large',t.scaleLarge);setOptionText('#executionPolicy','auto',t.auto);setOptionText('#executionPolicy','local_only',t.localOnly);setOptionText('#executionPolicy','prefer_local',t.preferLocal);setOptionText('#executionPolicy','remote_allowed',t.remoteAllowed);setOptionText('#executionPolicy','remote_only',t.remoteOnly);setOptionText('#tonePreset','normal',t.toneNormal);setOptionText('#tonePreset','friendly',t.toneFriendly);setOptionText('#tonePreset','ironic',t.toneIronic);setOptionText('#tonePreset','meme',t.toneMeme+' ⚡');setOptionText('#tonePreset','serious',t.toneSerious);setOptionText('#tonePreset','expert',t.toneExpert);setOptionText('#tonePreset','brief',t.toneBrief);setOptionText('#tonePreset','detailed',t.toneDetailed);
  setText('#runtimeRetry',t.retry);setText('#tourSkip',t.tourSkip);setText('#tourBack',t.tourBack);if($('#feedbackMessage'))$('#feedbackMessage').placeholder=lang==='en'?'What should be improved?':'Что улучшить?';if($('#sidebarResizer'))$('#sidebarResizer').setAttribute('aria-label',lang==='en'?'Resize sidebar':'Изменить ширину боковой панели');if($('#collapseSidebar'))$('#collapseSidebar').setAttribute('aria-label',lang==='en'?'Collapse sidebar':'Свернуть боковую панель');if($('#userGuideLink'))$('#userGuideLink').href=lang==='en'?'/static/user-guide.en.html':'/static/user-guide.html';if($('#whyLink'))$('#whyLink').href=lang==='en'?'/static/why.en.html':'/static/why.html';if($('#localSetupLink'))$('#localSetupLink').href=lang==='en'?'/static/local-setup.en.html':'/static/local-setup.html';translateExact($('#settingsModal'),lang);translateExact($('#helpBackdrop'),lang);translateExact($('#chatMenu'),lang);renderAll();renderToneMenu();updateRuntimeStateCopy();
}
const STATIC_EN={
 'Очистить':'Clear','Профиль':'Profile','Администрирование ↗':'Administration ↗','История диалогов хранится сервером и переживает очистку кэша браузера и перезапуск Core. Экспорт создаёт проверенный файл в вашем workspace.':'Conversation history is stored by the server and survives browser cache cleanup and Core restarts. Export creates a verified file in your workspace.','Поделиться текущим чатом':'Share current chat','Скачать текущий чат (.md)':'Download current chat (.md)','Экспортировать все диалоги (.json)':'Export all chats (.json)','Очистить текущий чат':'Clear current chat','Удалить все диалоги':'Delete all chats','Auto использует эти предпочтения при сценариях и обычных веб-запросах. Техническую стратегию сайтов настраивает администратор.':'Auto uses these preferences for scenarios and ordinary web requests. Technical site strategies are managed by the administrator.','Область поиска':'Search scope','Весь интернет':'Entire web','Предпочитать российские сайты':'Prefer Russian sites','Только выбранные сайты':'Selected sites only','Город / регион':'City / region','Искать только на сайтах':'Search only these sites','Не использовать сайты':'Do not use sites','Поднимать российские источники выше, когда они релевантны':'Prefer Russian sources when relevant','Сохранить настройки поиска':'Save search preferences','Загруженные и созданные файлы хранятся в изолированном workspace вашего профиля и проверяются перед выдачей.':'Uploaded and generated files are stored in your isolated workspace and verified before delivery.','Формат':'Format','Имя файла':'File name','Содержимое':'Content','Создать и проверить':'Create and verify','Загрузить файл':'Upload file','Код выполняется в отдельном sandbox-worker без сети и без доступа к Docker socket, Core, базе данных или вашим секретам.':'Code runs in an isolated sandbox worker without network access and without access to Docker socket, Core, the database or your secrets.','Язык':'Language','Лимит времени':'Time limit','Запустить':'Run','Отменить':'Cancel','Задачи и прогресс':'Tasks & progress','Обновить задачи':'Refresh tasks','Помощь и возможности':'Help & capabilities','Пройти обучение':'Start guided tour','Руководство':'Guide','Установить локальный AI':'Set up local AI','Подтверждение':'Confirmation','Отмена':'Cancel','Продолжить':'Continue','Обратная связь':'Feedback','Тип':'Type','Оценка':'Rating','Сообщение':'Message','Отправить':'Send','Версия интерфейса':'UI version','Должна совпадать с Core':'Must match Core','Локальный AI-помощник, который умеет работать с интернетом, файлами, кодом и проверяемыми результатами — без необходимости разбираться в инфраструктуре.':'A local-first AI assistant for web, files, code and verified results — without requiring infrastructure knowledge.','▶ Пройти обучение':'▶ Start guided tour','Пошагово покажем интерфейс за пару минут.':'A short interactive walkthrough of the interface.','Основные сценарии и ответы на вопросы.':'Core workflows and common questions.','Что умеет Родной Агент':'What Personal Agent can do','Чат, интернет, файлы, код, задачи и приватность.':'Chat, web, files, code, tasks and privacy.','Почему Родной Агент':'Why Personal Agent','Чем local-first агент отличается от обычного AI-чата.':'How a local-first agent differs from a regular AI chat.','Пошаговый старт на Windows: Docker, модель, проверка и LAN.':'Step-by-step Windows setup: runtime, model, verification and LAN.','Ненавязчиво сообщить идею, ошибку или оценить качество.':'Send an idea, bug report or quality rating without leaving the product.','Не прикладывайте пароли, API-ключи и приватные документы. Сообщение сохранится локально/на вашем сервере для администратора.':'Do not include passwords, API keys or private documents. The message is stored locally/on your server for an administrator.','Идея':'Idea','Ошибка':'Bug','Качество ответа':'Answer quality','Интерфейс':'Interface','Другое':'Other','Без оценки':'No rating','5 — отлично':'5 — excellent','1 — плохо':'1 — poor','Что улучшить?':'What should be improved?','Русский':'Russian','«Только локально» запрещает скрытый remote fallback. «Мемный» меняет подачу, но не требования к точности и проверке.':'“Local only” prevents hidden remote fallback. “Meme” changes presentation, never accuracy or verification requirements.'};
function translateExact(container,lang){if(!container)return;const forward=STATIC_EN,reverse=Object.fromEntries(Object.entries(forward).map(([a,b])=>[b,a]));const map=lang==='en'?forward:reverse;const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);for(const textNode of nodes){const raw=textNode.textContent,trimmed=raw.trim();if(!trimmed||!map[trimmed])continue;textNode.textContent=raw.replace(trimmed,map[trimmed])}}
function renderExperiencePreferences(){const p=state.experiencePreferences||{};if($('#uiLanguage'))$('#uiLanguage').value=p.ui_language||'ru';if($('#responseLanguage'))$('#responseLanguage').value=p.response_language||'auto';if($('#themeSelect'))$('#themeSelect').value=p.theme||'system';if($('#uiScale'))$('#uiScale').value=p.ui_scale||'normal';if($('#executionPolicy'))$('#executionPolicy').value=p.execution_policy||'auto';if($('#tonePreset'))$('#tonePreset').value=p.tone||'normal';if($('#executionQuickLabel'))$('#executionQuickLabel').textContent=executionLabel(p.execution_policy||'auto');applyTheme(p.theme||'system');applyUiScale(p.ui_scale||'normal');applyLanguage(p.ui_language||'ru')}
async function loadExperiencePreferences(){try{const payload=await api('/api/preferences/experience');state.experiencePreferences=payload.preferences||{};renderExperiencePreferences()}catch(_){state.experiencePreferences={ui_language:localStorage.getItem('par-ui-language')||'ru',response_language:'auto',theme:localStorage.getItem('par-theme-preference')||'system',execution_policy:'auto',tone:'normal',ui_scale:localStorage.getItem('par-ui-scale')||'normal'};renderExperiencePreferences()}}
async function saveExperiencePreferences(){const out=$('#experienceState');try{const payload=await api('/api/preferences/experience',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ui_language:$('#uiLanguage').value,response_language:$('#responseLanguage').value,theme:$('#themeSelect').value,ui_scale:$('#uiScale').value,execution_policy:$('#executionPolicy').value,tone:$('#tonePreset').value})});state.experiencePreferences=payload.preferences;renderExperiencePreferences();out.textContent=tr('saved');out.className='job-state completed';toast(langKey()==='en'?'Settings saved':'Настройки сохранены','success')}catch(error){out.textContent=friendlyError(error).title;out.className='job-state failed'}}
async function shareCurrent(){const c=current();if(!c||!c.messages.length){toast(L('В текущем диалоге пока нечем делиться','There is nothing to share in this chat yet'),'info');return}const ttl=await selectAction(L('Поделиться диалогом','Share chat'),L('Будет создан отдельный read-only снимок. Ссылка не даёт доступ к аккаунту, другим чатам или workspace.','A separate read-only snapshot will be created. The link does not grant access to the account, other chats or workspace.'),[{value:'86400',label:L('1 день','1 day')},{value:'604800',label:L('7 дней','7 days')},{value:'2592000',label:L('30 дней','30 days')}],'604800',L('Создать ссылку','Create link'));if(ttl===null)return;try{const payload=await api(`/api/conversations/${c.id}/share`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ttl_seconds:Number(ttl)})});const share=payload.share;if(navigator.share){try{await navigator.share({title:share.title,text:`${tr('brand')}: ${share.title}`,url:share.url});toast(L('Открыто системное меню «Поделиться»','System share menu opened'),'success');return}catch(error){if(error?.name==='AbortError')return}}await copyText(share.url);setBanner(L('Создан приватный снимок диалога. Ссылка не даёт доступ к аккаунту или workspace.','A private chat snapshot was created. The link does not grant access to the account or workspace.'),'info')}catch(error){toast(error.message,'error')}}
async function sendFeedback(){const out=$('#feedbackState');try{const payload=await api('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({category:$('#feedbackCategory').value,rating:$('#feedbackRating').value||null,message:$('#feedbackMessage').value,page:location.pathname})});$('#feedbackMessage').value='';out.textContent=L('Спасибо! Сохранено.','Thank you! Saved.');out.className='job-state completed';toast(L('Спасибо за обратную связь','Thanks for your feedback'),'success')}catch(error){out.textContent=error.message;out.className='job-state failed'}}

async function init(){
  loadStore();bindEvents();resizeInput();showRuntimeState('booting',tr('runtimeStartingTitle'),tr('runtimeStartingDetail'));chat.setAttribute('aria-busy','true');
  try{
    state.system=await api('/api/system');
    try{state.auth=await api('/api/auth/me')}catch(_){state.auth={ok:false,mode:state.system?.auth?.mode||'personal'}}
    if(!enforceUiVersion(state.system.version))return;
    $('#version').textContent=`v${state.system.version}`;$('#settingsVersion').textContent=`v${state.system.version}`;
    const account=$('#accountEntry');if(account){if(state.auth?.user){account.href='/account';account.querySelector('.account-label').textContent=state.auth.user.display_name||'Аккаунт'}else if(state.system?.auth?.mode==='accounts'){account.href='/login';account.querySelector('.account-label').textContent=L('Войти','Sign in')}else{account.href='/account';account.querySelector('.account-label').textContent=L('Локальный профиль','Local profile')}}
    const role=String(state.auth?.user?.role||'').toUpperCase();const roleAdmin=['OWNER','ADMIN'].includes(role);const personalOwner=state.system?.auth?.mode==='personal';$('#adminEntry').hidden=personalOwner||!roleAdmin;const adminSettings=$('#adminSettingsLink');if(adminSettings)adminSettings.hidden=!(roleAdmin||personalOwner);
    applySidebarPreferences();
    await loadExperiencePreferences();
    try{const scenarioPayload=await api('/api/scenarios');state.scenarios=scenarioPayload.scenarios||[]}catch(_){state.scenarios=[]}
    try{const prefPayload=await api('/api/preferences/web');state.webPreferences=prefPayload.preferences||null;renderWebPreferences()}catch(_){state.webPreferences=null}
    await loadServerStore();await loadArtifacts();await health();await maybeStartTour();
  }catch(error){const friendly=friendlyError(error);setHealth(false,friendly.title);showRuntimeState(friendly.kind,friendly.title,friendly.detail);console.error(error)}
  chat.setAttribute('aria-busy','false');requestAnimationFrame(()=>document.body.classList.add('ui-ready'));input.focus();
}
function linesToDomains(value){return String(value||'').split(/\r?\n|,/).map(x=>x.trim().toLowerCase()).filter(Boolean)}
function renderWebPreferences(){const p=state.webPreferences||{};if($('#webSearchScope'))$('#webSearchScope').value=p.search_scope||'internet';if($('#webRegion'))$('#webRegion').value=p.region||'';if($('#webAllowedDomains'))$('#webAllowedDomains').value=(p.allowed_domains||[]).join('\n');if($('#webExcludedDomains'))$('#webExcludedDomains').value=(p.excluded_domains||[]).join('\n');if($('#webNewsInterests'))$('#webNewsInterests').value=(p.news_interests||[]).join('\n');if($('#webPreferRussian'))$('#webPreferRussian').checked=p.prefer_russian!==false}
async function saveWebPreferences(){try{const payload=await api('/api/preferences/web',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({search_scope:$('#webSearchScope').value,region:$('#webRegion').value,allowed_domains:linesToDomains($('#webAllowedDomains').value),excluded_domains:linesToDomains($('#webExcludedDomains').value),news_interests:String($('#webNewsInterests')?.value||'').split(/\r?\n|,/).map(x=>x.trim()).filter(Boolean),prefer_russian:$('#webPreferRussian').checked})});state.webPreferences=payload.preferences;renderWebPreferences();toast(L('Настройки поиска сохранены','Search preferences saved'),'success')}catch(error){toast(error.message,'error')}}
async function health(){try{const result=await api('/api/health');const ready=Boolean(result.ready);const degraded=['web_search','browser','code'].some(key=>String(result[key]||'').toLowerCase()==='degraded');setHealth(ready,!ready?tr('starting'):degraded?tr('runtimeDegradedTitle'):tr('ready'));if(!ready)showRuntimeState('starting',tr('runtimeStartingTitle'),tr('runtimeStartingDetail'));else if(degraded)showRuntimeState('degraded',tr('runtimeDegradedTitle'),tr('runtimeDegradedDetail'));else showRuntimeState('ready','','')}catch(error){setHealth(false,tr('offline'));showRuntimeState('offline',tr('runtimeOfflineTitle'),tr('runtimeOfflineDetail'))}}
function setHealth(ok,text){for(const selector of ['#dot','#sideDot'])$(selector).className=`dot ${ok?'ok':'bad'}`;$('#health').textContent=text;$('#sideHealth').textContent=text}
function resizeInput(){input.style.height='auto';input.style.height=`${Math.min(200,Math.max(44,input.scrollHeight))}px`}
function openSidebar(){document.body.classList.add('sidebar-open')}
function closeSidebar(){document.body.classList.remove('sidebar-open')}

function toast(message,type='info'){
  const item=node('div',`toast ${type}`,message);$('#toasts').append(item);setTimeout(()=>item.classList.add('show'),10);setTimeout(()=>{item.classList.remove('show');setTimeout(()=>item.remove(),180)},2600);
}
async function copyText(text,button){
  let ok=false;
  try{if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(String(text));ok=true}}catch(_){}
  if(!ok){
    const area=document.createElement('textarea');area.value=String(text);area.style.position='fixed';area.style.opacity='0';document.body.append(area);area.select();try{ok=document.execCommand('copy')}catch(_){}area.remove();
  }
  if(button){const previous=button.textContent;button.textContent=ok?'Скопировано':'Выделено';setTimeout(()=>button.textContent=previous,1200)}
  toast(ok?'Скопировано в буфер':'Текст готов к копированию',ok?'success':'info');
}
function downloadFile(name,type,content){
  const blob=new Blob([content],{type});const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=name;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast(`Экспортировано: ${name}`,'success');
}
function safeFilename(value){return String(value||'chat').replace(/[\\/:*?"<>|]+/g,'-').replace(/\s+/g,' ').trim().slice(0,64)||'chat'}
function chatMarkdown(c){
  const lines=[`# ${c.title}`,'',`${L('Экспорт Персонального агента','Personal Agent export')} · ${new Date().toLocaleString(langKey()==='en'?'en-US':'ru-RU')}`,''];
  for(const message of c.messages){
    lines.push(`## ${message.role==='user'?L('Вы','You'):tr('brand')}`,'',message.content,'');
    if(Array.isArray(message.sources)&&message.sources.length){lines.push('### Источники','');for(const source of message.sources){lines.push(`- [${source.title||source.url}](${source.url})${source.published_date?` · ${source.published_date}`:''}`)}lines.push('')}
    if(Array.isArray(message.attachments)&&message.attachments.length){lines.push('### Файлы','');for(const file of message.attachments){lines.push(`- ${file.name||'Файл'}${file.sha256?` · SHA-256 ${file.sha256}`:''}`)}lines.push('')}
  }
  return lines.join('\n');
}
function triggerArtifactDownload(artifact){
  const anchor=document.createElement('a');anchor.href=artifact.download_url||`/api/files/${artifact.artifact_id}/download`;anchor.download=artifact.name||'';anchor.rel='noopener';document.body.append(anchor);anchor.click();anchor.remove();
}
async function persistExport(format,name,content){
  const payload=await api('/api/files/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({format,name,content})});
  if(!payload?.artifact?.artifact_id)throw new Error('Сервер не вернул файл экспорта');
  triggerArtifactDownload(payload.artifact);await loadArtifacts();return payload.artifact;
}
async function exportCurrent(){
  const c=current();if(!c||!c.messages.length){toast('В текущем диалоге пока нечего экспортировать','info');return}
  const name=`${safeFilename(c.title)}.md`;const content=chatMarkdown(c);
  try{const artifact=await persistExport('md',name,content);toast(`Чат сохранён в workspace: ${artifact.name}`,'success')}
  catch(error){downloadFile(name,'text/markdown;charset=utf-8',content);setBanner(`Серверный экспорт недоступен (${error.message}). Использован локальный Markdown-файл.`,'warning')}
}
async function exportAll(){
  const name=`personal-agent-rus-chats-${new Date().toISOString().slice(0,10)}.json`;const server=await api('/api/conversations/export');const payload={product:'Personal Agent Rus',version:UI_VERSION,exported_at:new Date().toISOString(),schema_version:server.export?.schema_version||1,folders:server.export?.folders||[],conversations:server.export?.conversations||[]};const content=JSON.stringify(payload,null,2);
  try{const artifact=await persistExport('json',name,payload);toast(`Архив диалогов сохранён: ${artifact.name}`,'success')}
  catch(error){downloadFile(name,'application/json;charset=utf-8',content);setBanner(`Серверный экспорт недоступен (${error.message}). Использован локальный JSON-файл.`,'warning')}
}

let actionResolver=null;
function openActionModal({title,message,confirmText='Продолжить',danger=false,inputValue=null,inputLabel='Название',selectOptions=null,selectValue=''}){
  $('#actionTitle').textContent=title;$('#actionMessage').textContent=message||'';$('#actionConfirm').textContent=confirmText;$('#actionConfirm').className=danger?'danger-button':'primary-button';
  const field=$('#actionInput');const label=$('#actionInputLabel');const select=$('#actionSelect');const hasInput=inputValue!==null;const hasSelect=Array.isArray(selectOptions);
  field.hidden=!hasInput;label.hidden=!hasInput;if(hasInput){field.value=String(inputValue);label.textContent=inputLabel}
  select.hidden=!hasSelect;select.replaceChildren();if(hasSelect){for(const option of selectOptions){const item=node('option','',option.label);item.value=option.value;if(String(option.value)===String(selectValue))item.selected=true;select.append(item)}}
  $('#actionBackdrop').hidden=false;requestAnimationFrame(()=>{(hasInput?field:(hasSelect?select:$('#actionConfirm'))).focus();if(hasInput)field.select()});
  return new Promise(resolve=>{actionResolver=resolve});
}
function closeActionModal(result){$('#actionBackdrop').hidden=true;const resolver=actionResolver;actionResolver=null;if(resolver)resolver(result)}
async function confirmAction(title,message,confirmText='Продолжить',kind='normal'){return Boolean(await openActionModal({title,message,confirmText,danger:kind==='danger'}))}
async function promptAction(title,message,value,inputLabel=L('Название диалога','Chat title')){const result=await openActionModal({title,message,confirmText:'Сохранить',inputValue:value,inputLabel});return result===false?null:String(result||'').trim()}
async function selectAction(title,message,options,value='',confirmText='Выбрать'){const result=await openActionModal({title,message,confirmText,selectOptions:options,selectValue:value});return result===false?null:String(result)}

async function refreshCodeStatus(){
  const host=$('#codeRunState');if(!host)return;
  try{const result=await api('/api/code/status');const ready=(result.languages||[]).filter(x=>x.available).map(x=>x.label).join(', ');host.textContent=result.ready?`Sandbox готов · ${ready} · сеть отключена`:`Sandbox частично доступен · ${ready}`;host.dataset.state=result.ready?'ready':'degraded'}catch(error){host.textContent=`Sandbox недоступен: ${error.message}`;host.dataset.state='error'}
}
function renderCodeJob(job){
  const stateHost=$('#codeRunState');const out=$('#codeStdout');const err=$('#codeStderr');
  const result=job?.result||{};const compile=job?.compile||{};
  const pieces=[job?.status||'UNKNOWN',job?.language||''];if(result.duration_ms!=null)pieces.push(`${result.duration_ms} ms`);if(result.exit_code!=null)pieces.push(`exit ${result.exit_code}`);
  stateHost.textContent=pieces.filter(Boolean).join(' · ')+(job?.error?` · ${job.error}`:'');
  out.textContent=[compile.stdout,result.stdout].filter(Boolean).join('\n');
  err.textContent=[compile.stderr,result.stderr].filter(Boolean).join('\n');
  const done=['COMPLETED','FAILED','CANCELLED'].includes(job?.status);$('#runCode').disabled=!done;$('#cancelCode').disabled=done;
}
async function pollCodeJob(){
  if(!state.codeJobId)return;
  try{const payload=await api(`/api/code/jobs/${state.codeJobId}`);renderCodeJob(payload.job);if(['COMPLETED','FAILED','CANCELLED'].includes(payload.job.status)){state.codeJobId=null;state.codePollTimer=null;return}}catch(error){$('#codeRunState').textContent=error.message;state.codeJobId=null;$('#runCode').disabled=false;$('#cancelCode').disabled=true;return}
  state.codePollTimer=setTimeout(pollCodeJob,250);
}
async function runCode(){
  const language=$('#codeLanguage').value;const code=$('#codeEditor').value;const timeout_seconds=Number($('#codeTimeout').value||10);if(!code.trim()){toast('Введите код','error');return}
  $('#runCode').disabled=true;$('#cancelCode').disabled=false;$('#codeStdout').textContent='';$('#codeStderr').textContent='';$('#codeRunState').textContent='Запускаю в изолированном sandbox…';
  try{const payload=await api('/api/code/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({language,code,timeout_seconds})});state.codeJobId=payload.job.id;renderCodeJob(payload.job);pollCodeJob()}catch(error){$('#runCode').disabled=false;$('#cancelCode').disabled=true;$('#codeRunState').textContent=error.message;toast(error.message,'error')}
}
async function cancelCode(){if(!state.codeJobId)return;try{const payload=await api(`/api/code/jobs/${state.codeJobId}/cancel`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});renderCodeJob(payload.job);state.codeJobId=null;if(state.codePollTimer)clearTimeout(state.codePollTimer)}catch(error){toast(error.message,'error')}}

function openSettings(tab='general'){$('#settingsBackdrop').hidden=false;selectSettingsTab(tab);$('#closeSettings').focus()}
function closeSettings(){$('#settingsBackdrop').hidden=true;$('#settingsEntry').focus()}
function selectSettingsTab(name){$$('[data-settings-tab]').forEach(button=>button.classList.toggle('active',button.dataset.settingsTab===name));$$('[data-settings-panel]').forEach(panel=>panel.classList.toggle('active',panel.dataset.settingsPanel===name))}
function toggleChatMenu(force){const menu=$('#chatMenu');const nextHidden=force===undefined?!menu.hidden:!force;if(!nextHidden){const c=current();const pin=menu.querySelector('[data-action="pin"]');const archive=menu.querySelector('[data-action="archive"]');if(pin)pin.textContent=c?.pinned_at?'Открепить':'Закрепить';if(archive)archive.textContent=c?.archived_at?'Вернуть из архива':'В архив'}menu.hidden=nextHidden;$('#chatMenuButton').setAttribute('aria-expanded',String(!nextHidden))}

function taskPhaseLabel(task){
  const labels=langKey()==='en'?{created:'Created',planning:'Planning',web:'Searching sources',analysis:'Analyzing',artifacts:'Creating files',verification:'Verifying result',completed:'Done',failed:'Error',cancelled:'Cancelled'}:{created:'Создано',planning:'Планирую',web:'Ищу источники',analysis:'Анализирую',artifacts:'Создаю файлы',verification:'Проверяю результат',completed:'Готово',failed:'Ошибка',cancelled:'Отменено'};
  return labels[task?.phase]||task?.phase||task?.status||L('Задача','Task');
}
function renderTaskList(){
  const host=$('#taskList');if(!host)return;host.replaceChildren();
  if(!state.tasks.length){host.append(node('div','muted',L('Задач пока нет.','No tasks yet.')));return}
  for(const task of state.tasks){const row=node('div','task-row');const copy=node('div','task-copy');copy.append(node('strong','',task.title||task.task_type),node('small','',`${task.status} · ${task.progress||0}% · ${taskPhaseLabel(task)}`));const actions=node('div','task-actions');if(!['COMPLETED','FAILED','CANCELLED','PARTIAL','BLOCKED'].includes(task.status)){const cancel=node('button','danger-button','Отменить');cancel.type='button';cancel.onclick=()=>cancelTask(task.id);actions.append(cancel)}row.append(copy,actions);host.append(row)}
}
async function loadTasks(){try{const result=await api('/api/tasks?limit=50');state.tasks=result.tasks||[];renderTaskList()}catch(_){state.tasks=[];renderTaskList()}}
async function cancelTask(taskId){try{await api(`/api/tasks/${taskId}/cancel`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});toast('Отмена запрошена','success');await loadTasks()}catch(error){toast(error.message,'error')}}
function updateTaskMessage(message,task){
  message.taskId=task.id;message.kind='task';message.content=`${taskPhaseLabel(task)} · ${task.progress||0}%`;
  if(task.status==='FAILED')message.content=`Задача завершилась ошибкой: ${task.error||'неизвестная ошибка'}`;
  if(task.status==='CANCELLED')message.content=L('Задача отменена.','Task cancelled.');
  if(task.status==='COMPLETED'){
    message.content=task.result?.answer||L('Готово. Результаты проверены.','Done. The results were verified.');
    message.sources=task.result?.sources||[];
    message.attachments=(task.result?.artifacts||[]).map(a=>({artifact_id:a.id,name:a.name,format:(a.name||'').split('.').pop()||'file',download_url:`/api/files/${a.id}/download`}));
  }
}
async function pollTask(taskId,message){
  try{const payload=await api(`/api/tasks/${taskId}`);const task=payload.task;updateTaskMessage(message,task);saveStore();renderAll();if(['COMPLETED','FAILED','CANCELLED','PARTIAL','BLOCKED'].includes(task.status)){delete state.taskPollTimers[taskId];state.taskMode=null;await loadTasks();return}}catch(error){message.content=`Не удалось обновить задачу: ${error.message}`;saveStore();renderAll();delete state.taskPollTimers[taskId];return}
  state.taskPollTimers[taskId]=setTimeout(()=>pollTask(taskId,message),700);
}
async function sendTaskRequest(content){
  const c=current();addMessage({role:'user',content});const progress=addMessage({role:'assistant',content:'Создаю задачу…',kind:'task'});try{await api(`/api/conversations/${c.id}/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:'user',content})})}catch(_){}setBusy(true);
  try{const payload=await api('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'research_report',question:content,formats:['md','xlsx','pdf']})});updateTaskMessage(progress,payload.task);saveStore();renderAll();pollTask(payload.task.id,progress);setBanner(L('Задача выполняется сервером: можно обновить страницу и вернуться позже.','The task is running on the server. You can refresh the page and return later.'),'info')}catch(error){progress.content=`${L('Не удалось создать задачу','Could not create task')}: ${error.message}`;progress.kind='error';saveStore();renderAll();state.taskMode=null}finally{setBusy(false);input.value='';resizeInput();input.focus()}
}
function toggleToolTray(force){const tray=$('#toolTray');const nextHidden=force===undefined?!tray.hidden:!force;tray.hidden=nextHidden;$('#attachBtn').setAttribute('aria-expanded',String(!nextHidden))}

async function renameCurrent(){const c=current();if(!c)return;const value=await promptAction(L('Переименовать диалог','Rename chat'),L('Название сохранится в Персональном агенте и будет доступно после перезапуска.','The title will be stored by Personal Agent and remain available after restart.'),c.title);if(value===null)return;const result=await api(`/api/conversations/${c.id}/rename`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:value||defaultChatTitle()})});const index=state.conversations.findIndex(x=>x.id===c.id);state.conversations[index]=serverConversation(result.conversation);renderAll();toast(L('Диалог переименован','Chat renamed'),'success')}
async function clearCurrent(){const c=current();if(!c||!c.messages.length){toast(L('Диалог уже пуст','Chat is already empty'));return}if(await confirmAction(L('Очистить сообщения?','Clear messages?'),L('Название диалога будет сброшено, сообщения удалятся с сервера.','The chat title will be reset and messages will be deleted from the server.'),L('Очистить','Clear'),'danger')){await clearCurrentNow();toast(L('Сообщения очищены','Messages cleared'),'success')}}
async function deleteCurrent(){const c=current();if(!c)return;if(await confirmAction(L('Удалить диалог?','Delete chat?'),L(`«${c.title}» будет удалён из вашей истории.`,`“${c.title}” will be deleted from your history.`),L('Удалить','Delete'),'danger')){await deleteConversationNow(c.id);toast(L('Диалог удалён','Chat deleted'),'success')}}
async function clearAll(){if(await confirmAction(L('Удалить все диалоги?','Delete all chats?'),L('Будет удалена вся история текущего пользователя. Файлы workspace не удаляются.','All chat history for the current user will be deleted. Workspace files will be kept.'),L('Удалить всё','Delete all'),'danger')){await clearAllNow();toast(L('История очищена','History cleared'),'success')}}
async function renameFolder(folder){const name=await promptAction(L('Переименовать проект','Rename project'),L('Новое название будет сохранено для всех ваших устройств.','The new name will be saved for all your devices.'),folder.name,L('Название проекта','Project name'));if(name===null||!name)return;const result=await api(`/api/folders/${folder.id}/rename`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});const index=state.folders.findIndex(x=>x.id===folder.id);if(index>=0)state.folders[index]=result.folder;renderAll();toast(L('Проект переименован','Project renamed'),'success')}
async function deleteFolder(folder){if(!await confirmAction(L('Удалить проект?','Delete project?'),L(`Диалоги из «${folder.name}» останутся в истории без проекта.`,`Chats from “${folder.name}” will remain in history without a project.`),L('Удалить проект','Delete project'),'danger'))return;await api(`/api/folders/${folder.id}`,{method:'DELETE'});if(state.activeFolderId===folder.id)state.activeFolderId=null;await loadServerStore(state.search);toast(L('Проект удалён, диалоги сохранены','Project deleted; chats were preserved'),'success')}
async function setConversationPinned(conversation,pinned){const result=await api(`/api/conversations/${conversation.id}/pin`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pinned})});const index=state.conversations.findIndex(x=>x.id===conversation.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);saveStore();renderAll();toast(pinned?L('Диалог закреплён','Chat pinned'):L('Диалог откреплён','Chat unpinned'),'success')}
async function moveCurrent(){const c=current();if(!c)return;const options=[{value:'',label:L('Без проекта','No project')},...state.folders.map(folder=>({value:folder.id,label:folder.name}))];const folderId=await selectAction(L('Переместить диалог','Move chat'),L('Выберите проект для текущего диалога.','Choose a project for the current chat.'),options,c.folder_id||'');if(folderId===null)return;const result=await api(`/api/conversations/${c.id}/move`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder_id:folderId||null})});const index=state.conversations.findIndex(x=>x.id===c.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);await loadServerStore(state.search);toast(folderId?L('Диалог перемещён в проект','Chat moved to project'):L('Диалог перемещён в «Все чаты»','Chat moved to All chats'),'success')}
async function archiveCurrent(){const c=current();if(!c)return;const archived=!Boolean(c.archived_at);const result=await api(`/api/conversations/${c.id}/archive`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({archived})});const index=state.conversations.findIndex(x=>x.id===c.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);if(archived&&state.activeFolderId!=='__archived__'){const next=state.conversations.find(x=>!x.archived_at&&x.id!==c.id);state.activeId=next?.id||null;if(!state.activeId)await newConversation(false)}await loadServerStore(state.search);toast(archived?L('Диалог перемещён в архив','Chat archived'):L('Диалог возвращён из архива','Chat restored from archive'),'success')}
async function createFolder(){const name=await promptAction(L('Новый проект','New project'),L('Проекты помогают группировать связанные диалоги.','Projects help group related chats.'),L('Новый проект','New project'),L('Название проекта','Project name'));if(name===null||!String(name).trim())return;const result=await api('/api/folders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});state.folders.push(result.folder);state.activeFolderId=result.folder.id;saveStore();renderAll();toast(L('Проект создан','Project created'),'success')}
async function sendRequest({addUser=true,text=null}={}){
  if(state.busy)return;
  let content=String(text??input.value).trim();if(addUser&&!content&&state.pendingFiles.length)content=L('Проанализируй приложенные файлы и выдели главное.','Analyze the attached files and highlight the key points.');if(addUser&&!content)return;
  setBanner('');
  if(addUser&&state.taskMode==='research_report'){await sendTaskRequest(content);return}
  if(addUser){const attachments=[...state.pendingFiles];addMessage({role:'user',content,attachments});state.pendingFiles=[];renderPendingFiles();input.value='';resizeInput()}
  setBusy(true);setThinking(true);
  const pendingIntent=state.intentHint;
  if(pendingIntent==='research')setBanner(L('Исследую: ищу источники → читаю страницы → сверяю факты → формирую вывод…','Researching: searching sources → reading pages → checking facts → building a conclusion…'),'info');
  else if(pendingIntent==='search'||/https?:\/\//i.test(content))setBanner(L('Ищу и читаю веб-источники. Ответ появится после синтеза фактов…','Searching and reading web sources. The answer will appear after the facts are synthesized…'),'info');
  try{
    const c=current();
    const history=c.messages.filter(message=>!String(message.kind||'').startsWith('capability')).map(({role,content})=>({role,content}));
    const fileIds=[...new Set(c.messages.flatMap(message=>(message.attachments||[]).map(item=>item.artifact_id)).filter(Boolean))].slice(-12);
    const result=await api('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:state.mode,preset:state.preset,intent_hint:state.intentHint,scenario_id:state.scenarioId||'',file_ids:fileIds,messages:history,conversation_id:c.id,persist_user:addUser,attachments:addUser?(c.messages.at(-1)?.attachments||[]):[]})});
    const received=addMessage({...result.message,sources:result.sources||[]});if(received&&result.intent!=='clarification')state.animateMessageId=received.id;if(result.intent!=='clarification')state.scenarioId=null;else if(result.scenario?.id)state.scenarioId=result.scenario.id;state.intentHint='auto';setBanner(result.intent==='clarification'?(langKey()==='en'?'One short clarification is needed — after your answer Personal Agent will continue the task.':'Нужно одно короткое уточнение — после ответа Родной Агент продолжит задачу.'):'');try{await loadServerStore(state.search)}catch(_){}if((result.sources||[]).length)toast(`${L('Ответ собран по','Answer synthesized from')} ${result.sources.length} ${L('веб-источникам','web sources')}`,'success');
  }catch(error){
    if(error.code==='capability_unavailable'){
      const c=current();const last=[...(c?.messages||[])].reverse().find(message=>message.role==='user'&&message.kind==='message');if(last)last.kind='capability-request';saveStore();
      addMessage({role:'assistant',content:error.message||L('Для этого запроса нужна возможность, которая пока не подключена.','This request needs a capability that is not connected yet.'),kind:'capability'});
      setBanner(L('Запрос остановлен до обращения к локальной модели: требуется отдельная capability.','The request was stopped before local inference because a separate capability is required.'),'warning');
    }else{
      const friendly=friendlyError(error);addMessage({role:'assistant',content:`${friendly.title}. ${friendly.detail}`,kind:'error'});setBanner(friendly.detail,'warning');showRuntimeState(friendly.kind,friendly.title,friendly.detail);
    }
  }finally{setThinking(false);setBusy(false);input.focus()}
}
async function regenerateAt(index){
  if(state.busy)return;
  const c=current();if(!c)return;
  let assistantIndex=Math.min(index,c.messages.length-1);
  while(assistantIndex>=0&&c.messages[assistantIndex]?.role!=='assistant')assistantIndex--;
  if(assistantIndex<0)return;
  let userIndex=assistantIndex-1;while(userIndex>=0&&c.messages[userIndex]?.role!=='user')userIndex--;
  if(userIndex<0)return;
  c.messages.splice(assistantIndex,1);c.updatedAt=now();saveStore();renderAll();toast(L('Повторяю последний ответ','Retrying the last answer'));await sendRequest({addUser:false,text:c.messages[userIndex].content});
}

const TOUR_STEPS=[
  {selector:'#brandHelp',title:'Добро пожаловать в Родной Агент',title_en:'Welcome to Personal Agent',text:'Здесь можно пройти обучение заново, открыть руководство и быстро посмотреть возможности продукта.',text_en:'Restart the guided tour, open the guide and quickly explore the product capabilities here.'},
  {selector:'#newChat',title:'Новый чат',title_en:'New chat',text:'Создайте отдельный диалог. Быстрая клавиша — Ctrl+N.',text_en:'Start a separate conversation. Shortcut: Ctrl+N.'},
  {selector:'#input',title:'Просто напишите задачу',title_en:'Just describe the task',text:'Опишите результат обычным языком. Родной Агент сам выберет нужные возможности.',text_en:'Describe the outcome in plain language. Personal Agent will choose the required capabilities.'},
  {selector:'#attachBtn',title:'Файлы и инструменты',title_en:'Files and tools',text:'Прикрепляйте документы или включайте Web, Code и длинные задачи.',text_en:'Attach documents or enable Web, Code and long-running tasks.'},
  {selector:'#chatSearch',title:'История и поиск',title_en:'History and search',text:'Диалоги теперь хранятся на сервере и находятся по заголовку и содержимому.',text_en:'Chats are stored by the server and can be found by title or message content.'},
  {selector:'#newFolder',title:'Проекты',title_en:'Projects',text:'Группируйте связанные диалоги в проекты. Новый чат создаётся в выбранном проекте.',text_en:'Group related chats into projects. New chats are created in the selected project.'},
  {selector:'#exportChatButton',title:'Результат можно забрать',title_en:'Take the result with you',text:'Скачивайте текущий чат как проверенный Markdown-артефакт.',text_en:'Download the current chat as a verified Markdown artifact.'},
  {selector:'#executionQuick',title:'Приватность понятна сразу',title_en:'Privacy at a glance',text:'Локальный режим означает, что базовая обработка идёт на вашем компьютере. Remote-переходы должны быть явными.',text_en:'Local mode keeps the base processing on your computer. Any switch to remote processing must be explicit.'},
  {selector:'#accountEntry',title:'Профиль и тариф',title_en:'Profile and plan',text:'Здесь находятся аккаунт, подписка, использование и пользовательские настройки.',text_en:'Your account, subscription, usage and personal settings are available here.'}
];
let tourIndex=0;
function applySidebarPreferences(){const width=Math.max(240,Math.min(420,Number(localStorage.getItem('par-sidebar-width')||282)));document.documentElement.style.setProperty('--sidebar-user',`${width}px`);const collapsed=localStorage.getItem('par-sidebar-collapsed')==='1';$('#sidebar').classList.toggle('collapsed',collapsed);if(collapsed)document.documentElement.style.setProperty('--sidebar-user','68px')}
function setSidebarCollapsed(value){localStorage.setItem('par-sidebar-collapsed',value?'1':'0');applySidebarPreferences();const button=$('#collapseSidebar');button.textContent=value?'›':'‹';button.setAttribute('aria-expanded',String(!value));button.title=value?(langKey()==='en'?'Expand sidebar (Ctrl+B)':'Развернуть панель (Ctrl+B)'):(langKey()==='en'?'Collapse sidebar (Ctrl+B)':'Свернуть панель (Ctrl+B)')}
function setSidebarWidth(width){const next=Math.max(240,Math.min(420,Number(width)||282));document.documentElement.style.setProperty('--sidebar-user',`${next}px`);localStorage.setItem('par-sidebar-width',String(next));return next}
function bindSidebarResize(){const handle=$('#sidebarResizer');let active=false;handle.tabIndex=0;handle.setAttribute('aria-valuemin','240');handle.setAttribute('aria-valuemax','420');handle.addEventListener('pointerdown',event=>{active=true;handle.classList.add('dragging');handle.setPointerCapture(event.pointerId)});handle.addEventListener('pointermove',event=>{if(!active)return;const width=setSidebarWidth(event.clientX);handle.setAttribute('aria-valuenow',String(width))});const stop=()=>{active=false;handle.classList.remove('dragging')};handle.addEventListener('pointerup',stop);handle.addEventListener('pointercancel',stop);handle.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();let current=Number(localStorage.getItem('par-sidebar-width')||282);if(event.key==='Home')current=240;else if(event.key==='End')current=420;else current+=event.key==='ArrowRight'?16:-16;const width=setSidebarWidth(current);handle.setAttribute('aria-valuenow',String(width))})}
function openHelp(){closeSidebar();$('#helpBackdrop').hidden=false}
function closeHelp(){ $('#helpBackdrop').hidden=true }
function renderHelpCapabilities(){const host=$('#helpCapabilities');host.replaceChildren();for(const [key,item] of Object.entries(state.system?.capabilities||{})){const row=node('div','help-capability');row.append(node('span','',item.status==='ready'?'✓':'○'));const copy=node('div','');copy.append(node('strong','',item.label||key),node('small','',item.status==='ready'?L('Доступно сейчас','Available now'):item.status==='degraded'?L('Ограниченно доступно','Limited availability'):L('Подключается следующим слоем','Coming in a later layer')));row.append(copy);host.append(row)}host.hidden=false}
function tourTarget(){return document.querySelector(TOUR_STEPS[tourIndex]?.selector||'')}
function positionTour(){const target=tourTarget();if(!target)return;target.scrollIntoView({block:'center',inline:'nearest'});requestAnimationFrame(()=>{const rect=target.getBoundingClientRect();const pad=7;const spot=$('#tourSpotlight');Object.assign(spot.style,{left:`${Math.max(4,rect.left-pad)}px`,top:`${Math.max(4,rect.top-pad)}px`,width:`${Math.max(24,rect.width+pad*2)}px`,height:`${Math.max(24,rect.height+pad*2)}px`});const card=$('#tourCard');const w=Math.min(360,window.innerWidth-28);let left=rect.right+18;if(left+w>window.innerWidth-14)left=Math.max(14,rect.left-w-18);let top=Math.max(14,Math.min(window.innerHeight-230,rect.top));if(window.innerWidth<720){left=14;top=Math.max(14,window.innerHeight-250)}Object.assign(card.style,{left:`${left}px`,top:`${top}px`})})}
async function persistTour(status){try{await api('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona:'user',status,current_step:tourIndex})})}catch(_){}}
function renderTour(){const step=TOUR_STEPS[tourIndex];if(!step)return;$('#tourProgress').textContent=langKey()==='en'?`${tourIndex+1} of ${TOUR_STEPS.length}`:`${tourIndex+1} из ${TOUR_STEPS.length}`;$('#tourTitle').textContent=langKey()==='en'?(step.title_en||step.title):step.title;$('#tourText').textContent=langKey()==='en'?(step.text_en||step.text):step.text;$('#tourBack').disabled=tourIndex===0;$('#tourNext').textContent=tourIndex===TOUR_STEPS.length-1?tr('tourDone'):tr('tourNext');positionTour()}
async function startTour(force=false){closeHelp();if(!force){try{const value=await api('/api/onboarding');if(['completed','skipped'].includes(value.state?.status))return}catch(_){}}tourIndex=0;$('#tourLayer').hidden=false;await persistTour('in_progress');renderTour()}
async function finishTour(status='completed'){await persistTour(status);$('#tourLayer').hidden=true;input.focus()}
async function maybeStartTour(){await startTour(false)}

function bindEvents(){
  $('#runtimeRetry').onclick=()=>health();$('#newChat').onclick=()=>newConversation(true);$('#newFolder').onclick=createFolder;$('#brandHelp').onclick=openHelp;$('#helpEntry').onclick=openHelp;$('#feedbackEntry').onclick=()=>{openHelp();const box=$('#feedbackInline');if(box)box.hidden=false;setTimeout(()=>$('#feedbackMessage')?.focus(),0)};$('#closeHelp').onclick=closeHelp;$('#helpBackdrop').onclick=e=>{if(e.target===$('#helpBackdrop'))closeHelp()};$('#restartTour').onclick=()=>startTour(true);$('#showCapabilities').onclick=renderHelpCapabilities;$('#collapseSidebar').onclick=()=>setSidebarCollapsed(!$('#sidebar').classList.contains('collapsed'));bindSidebarResize();$('#openSidebar').onclick=openSidebar;$('#closeSidebar').onclick=closeSidebar;$('#sidebarBackdrop').onclick=closeSidebar;
  let searchTimer;$('#chatSearch').addEventListener('input',event=>{state.search=event.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadServerStore(state.search).catch(error=>toast(error.message,'warning')),180)});
  $('#clearAllShortcut').onclick=clearAll;
  $('#filesEntry').onclick=()=>{openSettings('files');loadArtifacts()};$('#codeEntry').onclick=()=>{openSettings('code');refreshCodeStatus()};$('#tasksEntry').onclick=()=>{openSettings('tasks');loadTasks()};$('#settingsEntry').onclick=()=>openSettings('general');$('#closeSettings').onclick=closeSettings;$('#settingsBackdrop').onclick=event=>{if(event.target===$('#settingsBackdrop'))closeSettings()};
  $$('[data-settings-tab]').forEach(button=>button.onclick=()=>selectSettingsTab(button.dataset.settingsTab));
  $('#exportCurrentChat').onclick=exportCurrent;$('#exportAllChats').onclick=exportAll;$('#clearCurrentChat').onclick=clearCurrent;$('#clearAllChats').onclick=clearAll;
  $('#runCode').onclick=runCode;$('#cancelCode').onclick=cancelCode;$('#refreshTasks').onclick=loadTasks;
  $('#fileInput').onchange=async event=>{await uploadSelectedFiles(event.target.files);event.target.value=''};$('#uploadArtifact').onclick=openFilePicker;$('#createArtifact').onclick=createArtifactFromUi;$('#artifactFormat').onchange=event=>{const fmt=event.target.value;const field=$('#artifactName');field.value=(field.value||'document').replace(/\.[^.]+$/, '')+`.${fmt}`};
  $('#exportChatButton').onclick=exportCurrent;$('#shareChatButton').onclick=shareCurrent;if($('#shareCurrentChat'))$('#shareCurrentChat').onclick=shareCurrent;if($('#executionQuick'))$('#executionQuick').onclick=()=>openSettings('general');$('#chatMenuButton').onclick=event=>{event.stopPropagation();toggleChatMenu()};
  $('#chatMenu').onclick=event=>{const item=event.target.closest('[data-action]');if(!item)return;toggleChatMenu(false);const action=item.dataset.action;if(action==='rename')renameCurrent();else if(action==='pin'){const c=current();if(c)setConversationPinned(c,!c.pinned_at)}else if(action==='move')moveCurrent();else if(action==='archive')archiveCurrent();else if(action==='share')shareCurrent();else if(action==='export')exportCurrent();else if(action==='clear')clearCurrent();else if(action==='delete')deleteCurrent()};
  if($('#saveWebPreferences'))$('#saveWebPreferences').onclick=saveWebPreferences;if($('#saveExperiencePreferences'))$('#saveExperiencePreferences').onclick=saveExperiencePreferences;if($('#openFeedback'))$('#openFeedback').onclick=()=>{$('#feedbackInline').hidden=!$('#feedbackInline').hidden;if(!$('#feedbackInline').hidden)$('#feedbackMessage').focus()};if($('#sendFeedback'))$('#sendFeedback').onclick=sendFeedback;$('#attachBtn').onclick=event=>{event.stopPropagation();toggleToolTray()};$('#modeButton').onclick=event=>{event.stopPropagation();const tones=$('#toneMenu');if(tones)tones.hidden=true;modes.hidden=!modes.hidden;$('#modeButton').setAttribute('aria-expanded',String(!modes.hidden))};$('#toneButton')?.addEventListener('click',event=>{event.stopPropagation();modes.hidden=true;const host=$('#toneMenu');host.hidden=!host.hidden;$('#toneButton').setAttribute('aria-expanded',String(!host.hidden))});
  $('#toolTray').onclick=event=>{const tool=event.target.closest('[data-tool]');if(!tool)return;toggleToolTray(false);const id=tool.dataset.tool;if(id==='web'){state.intentHint='search';setBanner(L('Веб включён для следующего запроса: поиск, чтение сайтов и источники.','Web is enabled for the next request: search, site reading and sources.'),'info');input.focus();return}if(id==='files'){openFilePicker();return}if(id==='code'){openSettings('code');refreshCodeStatus();return}if(id==='task-report'){state.taskMode='research_report';setBanner(L('Следующий запрос станет задачей: источники → анализ → MD/XLSX/PDF → проверка.','The next request will become a task: sources → analysis → MD/XLSX/PDF → verification.'),'info');input.focus();return}setBanner(`${tool.querySelector('strong')?.textContent||L('Эта возможность','This capability')} ${L('пока не подключена. Кнопка показана как честный preview будущей capability.','is not connected yet. The button is an honest preview of a future capability.')}`,'info')};
  $('#actionCancel').onclick=()=>closeActionModal(false);$('#actionConfirm').onclick=()=>{const field=$('#actionInput'),select=$('#actionSelect');closeActionModal(!field.hidden?field.value:(!select.hidden?select.value:true))};$('#actionBackdrop').onclick=event=>{if(event.target===$('#actionBackdrop'))closeActionModal(false)};
  $('#actionInput').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('#actionConfirm').click()}});
  input.addEventListener('input',resizeInput);input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('#form').requestSubmit()}});
  $('#form').onsubmit=event=>{event.preventDefault();sendRequest()};
  document.addEventListener('click',event=>{if(!event.target.closest('.menu-wrap'))toggleChatMenu(false);if(!event.target.closest('#toolTray')&&!event.target.closest('#attachBtn'))toggleToolTray(false);if(!event.target.closest('.composer-mode-wrap')){modes.hidden=true;$('#modeButton').setAttribute('aria-expanded','false');const tones=$('#toneMenu');if(tones){tones.hidden=true;$('#toneButton')?.setAttribute('aria-expanded','false')}}});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'){if(!$('#tourLayer').hidden){finishTour('skipped');return}toggleChatMenu(false);toggleToolTray(false);closeHelp();if(!$('#actionBackdrop').hidden)closeActionModal(false);else if(!$('#settingsBackdrop').hidden)closeSettings();else closeSidebar()}
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='n'){event.preventDefault();newConversation(true)}else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();$('#chatSearch').focus()}else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='b'){event.preventDefault();setSidebarCollapsed(!$('#sidebar').classList.contains('collapsed'))}
  });
  $('#tourSkip').onclick=()=>finishTour('skipped');$('#tourBack').onclick=()=>{if(tourIndex>0){tourIndex--;persistTour('in_progress');renderTour()}};$('#tourNext').onclick=()=>{if(tourIndex>=TOUR_STEPS.length-1){finishTour('completed')}else{tourIndex++;persistTour('in_progress');renderTour()}};window.addEventListener('resize',()=>{if(!$('#tourLayer').hidden)positionTour()});
}

matchMedia('(prefers-color-scheme: light)').addEventListener?.('change',()=>{if((state.experiencePreferences?.theme||'system')==='system')applyTheme('system')});
applyTheme(localStorage.getItem('par-theme-preference')||'system');applyUiScale(localStorage.getItem('par-ui-scale')||'normal');
init();
setInterval(health,15000);
