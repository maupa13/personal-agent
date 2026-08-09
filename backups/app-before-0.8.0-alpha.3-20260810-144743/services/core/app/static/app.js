'use strict';

const UI_VERSION='0.8.0-alpha.3';
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
    sources:Array.isArray(message?.sources)?message.sources.slice(0,12).map(source=>({title:String(source?.title||'').slice(0,300),url:String(source?.url||'').slice(0,2000),status:String(source?.status||'').slice(0,40),strategy:String(source?.strategy||'').slice(0,40),published_date:String(source?.published_date||'').slice(0,100)})):[],
    attachments:Array.isArray(message?.attachments)?message.attachments.slice(0,12).map(item=>({artifact_id:String(item?.artifact_id||'').slice(0,64),name:String(item?.name||'Файл').slice(0,180),format:String(item?.format||'').slice(0,12),size:Number(item?.size)||0,download_url:String(item?.download_url||'').slice(0,400)})).filter(item=>item.artifact_id):[],
    createdAt:Number(message?.createdAt||message?.created_at)||now(),
  };
}
function normalizeConversation(conversation){
  return {
    id:String(conversation?.id||uid()),
    title:String(conversation?.title||'Новый чат').replace(/\s+/g,' ').trim().slice(0,80)||'Новый чат',
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
  if(!first)return 'Новый чат';
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
    try{await api('/api/conversations/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversations:state.legacyConversations})});localStorage.removeItem(STORAGE_KEY);localStorage.removeItem(LEGACY_STORAGE_KEY);localStorage.removeItem(LEGACY_CHAT);payload=await api('/api/conversations?include_archived=1')}catch(error){toast(`Не удалось перенести старую историю: ${error.message}`,'warning')}
  }
  state.folders=payload.folders||state.folders||[];
  if(query){state.searchMatches=new Set((payload.conversations||[]).map(item=>item.id));renderAll();return}
  state.searchMatches=null;state.conversations=(payload.conversations||[]).map(serverConversation);
  if(!state.conversations.length){const created=await api('/api/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Новый чат',folder_id:state.activeFolderId||null})});state.conversations=[serverConversation(created.conversation)]}
  if(!state.conversations.some(c=>c.id===state.activeId))state.activeId=state.conversations[0]?.id||null;if(state.activeId)await loadConversation(state.activeId,false);
  saveStore();renderAll();
}
async function loadConversation(conversationId,render=true){
  const payload=await api(`/api/conversations/${encodeURIComponent(conversationId)}`);const full=serverConversation(payload.conversation);const index=state.conversations.findIndex(c=>c.id===conversationId);if(index>=0)state.conversations[index]=full;else state.conversations.unshift(full);state.activeId=conversationId;saveStore();if(render)renderAll();return full;
}
async function newConversation(render=true){
  const active=current();if(active&&active.messages?.length===0){state.activeId=active.id}else{const created=await api('/api/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Новый чат',folder_id:state.activeFolderId||null})});state.conversations.unshift(serverConversation(created.conversation));state.activeId=created.conversation.id}
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
function node(tag,className,text){
  const element=document.createElement(tag);
  if(className)element.className=className;
  if(text!==undefined)element.textContent=String(text);
  return element;
}
function relativeTime(timestamp){
  const delta=Math.max(0,Date.now()-Number(timestamp||0));
  if(delta<60000)return 'сейчас';
  if(delta<3600000)return `${Math.floor(delta/60000)} мин`;
  if(delta<86400000)return `${Math.floor(delta/3600000)} ч`;
  return new Date(timestamp).toLocaleDateString('ru-RU',{day:'2-digit',month:'short'});
}
function dateGroup(timestamp){const d=new Date(Number(timestamp||0));const nowD=new Date();const day=new Date(nowD.getFullYear(),nowD.getMonth(),nowD.getDate());const other=new Date(d.getFullYear(),d.getMonth(),d.getDate());const delta=Math.floor((day-other)/86400000);if(delta<=0)return 'Сегодня';if(delta===1)return 'Вчера';if(delta<7)return 'Последние 7 дней';return 'Ранее'}
function renderFolders(){
  const host=$('#folders');if(!host)return;host.replaceChildren();
  const all=node('button',`folder-item${!state.activeFolderId?' active':''}`);all.type='button';all.append(node('span','folder-icon','▦'),node('span','folder-copy','Все чаты'));all.onclick=()=>{state.activeFolderId=null;saveStore();renderAll()};host.append(all);
  for(const folder of state.folders){
    const row=node('div',`folder-item${state.activeFolderId===folder.id?' active':''}`);row.dataset.folderId=folder.id;
    const select=node('button','folder-select');select.type='button';const copy=node('span','folder-copy');copy.append(node('strong','',folder.name),node('small','',folder.conversation_count||0));select.append(node('span','folder-icon','▱'),copy);select.onclick=()=>{state.activeFolderId=folder.id;saveStore();renderAll()};
    const actions=node('span','folder-actions');const rename=node('button','folder-mini','✎');rename.type='button';rename.title='Переименовать проект';rename.onclick=event=>{event.stopPropagation();renameFolder(folder)};const remove=node('button','folder-mini','×');remove.type='button';remove.title='Удалить проект';remove.onclick=event=>{event.stopPropagation();deleteFolder(folder)};actions.append(rename,remove);row.append(select,actions);host.append(row);
  }
  const archivedCount=state.conversations.filter(c=>c.archived_at).length;const archive=node('button',`folder-item archive-item${state.activeFolderId==='__archived__'?' active':''}`);archive.type='button';archive.append(node('span','folder-icon','□'),node('span','folder-copy',`Архив${archivedCount?` · ${archivedCount}`:''}`));archive.onclick=async()=>{state.activeFolderId='__archived__';const first=state.conversations.find(c=>c.archived_at);if(first)await loadConversation(first.id,false);saveStore();renderAll()};host.append(archive);
}
function renderConversations(){
  conversationList.replaceChildren();renderFolders();const visible=state.conversations.filter(c=>{const archive=Boolean(c.archived_at);const scope=state.activeFolderId==='__archived__'?archive:(!archive&&(!state.activeFolderId||c.folder_id===state.activeFolderId));return scope&&(!state.search||state.searchMatches?.has(c.id))});const groups=new Map();for(const c of visible){const key=dateGroup(c.updatedAt);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(c)}
  for(const [label,items] of groups){const section=node('div','conversation-group');section.append(node('div','conversation-group-title',label));for(const conversation of items){const row=node('div',`conversation-item${conversation.id===state.activeId?' active':''}`);row.dataset.id=conversation.id;row.setAttribute('role','button');row.tabIndex=0;row.onclick=()=>selectConversation(conversation.id);row.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();selectConversation(conversation.id)}};const icon=node('button','conversation-icon',conversation.pinned_at?'◆':'◌');icon.type='button';icon.title=conversation.pinned_at?'Открепить':'Закрепить';icon.onclick=async event=>{event.stopPropagation();await setConversationPinned(conversation,!conversation.pinned_at)};const copy=node('span','conversation-copy');copy.append(node('strong','',conversation.title),node('small','',relativeTime(conversation.updatedAt)));const remove=node('button','conversation-delete','×');remove.type='button';remove.title='Удалить диалог';remove.onclick=async event=>{event.stopPropagation();if(await confirmAction('Удалить диалог?',`«${conversation.title}» будет удалён из истории.`,'Удалить','danger')){try{await deleteConversationNow(conversation.id);toast('Диалог удалён','success')}catch(error){toast(error.message,'warning')}}};row.append(icon,copy,remove);section.append(row)}conversationList.append(section)}
  $('#conversationEmpty').hidden=visible.length!==0;
}
function capChip(label,status){
  const element=node('span',`cap-chip ${status}`);
  element.append(node('span','cap-dot',''),node('span','',`${label}${status==='planned'?' · скоро':''}`));
  return element;
}
function renderWelcome(){
  const wrap=node('div','welcome');
  wrap.append(node('div','welcome-mark','PA'),node('h1','','Чем займёмся?'),node('p','','Personal Agent Rus — локальный AI-интерфейс. Модели и технические детали остаются в администрировании.'));
  const cards=node('div','starter-grid');
  const prompts=[
    ['preset','explain','Объяснить','Разобрать сложную тему простыми словами'],
    ['preset','write','Написать','Подготовить текст, план или идею'],
    ['preset','analyze','Проанализировать','Сравнить варианты и сделать вывод'],
    ['intent','search','Найти','Найти актуальные данные и источники в интернете'],
    ['intent','research','Исследовать','Собрать несколько источников, сравнить и сделать вывод'],
  ];
  for(const [kind,id,title,description] of prompts){
    const active=kind==='preset'?state.preset===id:state.intentHint===id;
    const button=node('button',`starter-card${active?' active':''}`);button.type='button';button.dataset[kind==='preset'?'preset':'intent']=id;
    button.append(node('strong','',title),node('span','',description));
    button.onclick=()=>{if(kind==='preset'){state.preset=id;localStorage.setItem(PRESET_KEY,id);toast(`Режим задачи: ${title}`,'success')}else{state.intentHint=id;setBanner(id==='research'?'Следующий запрос будет выполнен как исследование с несколькими веб-источниками.':'Следующий запрос будет выполнен с веб-поиском.','info');toast(`Веб-режим: ${title}`,'success')}renderAll();input.focus()};
    cards.appendChild(button);
  }
  if(state.scenarios.length){
    wrap.append(node('h2','scenario-heading','Попробуйте решить задачу'));
    const gallery=node('div','scenario-grid');
    for(const item of state.scenarios.slice(0,8)){
      const card=node('button',`scenario-card${state.scenarioId===item.id?' active':''}`);card.type='button';card.dataset.scenario=item.id;
      card.append(node('span','scenario-icon',item.icon||'◇'));const copy=node('span','scenario-copy');copy.append(node('strong','',item.title),node('small','',item.description));card.append(copy);
      card.onclick=()=>{state.scenarioId=item.id;input.value=item.example_prompt||'';resizeInput();renderAll();input.focus();input.setSelectionRange(input.value.length,input.value.length);toast(`Помощник: ${item.title}`,'success')};gallery.append(card);
    }
    wrap.append(gallery);
  }
  const caps=node('div','capability-row');
  const capabilities=state.system?.capabilities||{chat:{status:'ready',label:'Чат'},web:{status:'planned',label:'Веб'},files:{status:'planned',label:'Файлы'}};
  for(const capability of Object.values(capabilities).slice(0,4))caps.append(capChip(capability.label||'Возможность',capability.status||'planned'));
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
    const copy=node('button','code-copy','Копировать');copy.type='button';
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
function renderSources(message){
  const sources=Array.isArray(message?.sources)?message.sources.filter(source=>source?.url):[];if(!sources.length)return null;
  const wrap=node('div','message-sources');wrap.append(node('div','sources-title',`Источники · ${sources.length}`));const list=node('div','source-list');
  for(const [index,source] of sources.entries()){const link=node('a','source-card');link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';const idx=node('span','source-index',String(index+1));const copy=node('span','source-copy');let label=source.title||source.url;try{label=source.title||new URL(source.url).hostname}catch(_){}const meta=[source.published_date,source.status||'retrieved',source.strategy||'web'].filter(Boolean).join(' · ');copy.append(node('strong','',label),node('small','',meta));link.append(idx,copy);list.append(link)}
  wrap.append(list);return wrap;
}
function prettySize(bytes){const value=Number(bytes)||0;if(value<1024)return `${value} Б`;if(value<1024*1024)return `${(value/1024).toFixed(1)} КБ`;return `${(value/1024/1024).toFixed(1)} МБ`}
function renderMessageAttachments(message){
  const items=Array.isArray(message?.attachments)?message.attachments:[];if(!items.length)return null;
  const wrap=node('div','message-attachments');
  for(const item of items){const link=node('a','message-file');link.href=item.download_url||`/api/files/${item.artifact_id}/download`;link.target='_blank';link.rel='noopener';link.append(node('span','',String(item.format||'file').toUpperCase()),node('span','',item.name||'Файл'));wrap.append(link)}
  return wrap;
}
function renderPendingFiles(){
  const bar=$('#attachmentBar');if(!bar)return;bar.replaceChildren();bar.hidden=state.pendingFiles.length===0;
  for(const item of state.pendingFiles){const chip=node('div','attachment-chip');chip.append(node('span','',String(item.format||'file').toUpperCase()));const copy=node('span','');copy.append(node('strong','',item.name),node('small','',prettySize(item.size)));const remove=node('button','','×');remove.type='button';remove.title='Убрать из следующего сообщения';remove.onclick=()=>{state.pendingFiles=state.pendingFiles.filter(x=>x.artifact_id!==item.artifact_id);renderPendingFiles()};chip.append(copy,remove);bar.append(chip)}
}
async function uploadSelectedFiles(files){
  for(const file of Array.from(files||[])){
    try{
      setBanner(`Загружаю и проверяю ${file.name}…`,'info');
      const response=await fetch('/api/files/upload',{method:'POST',headers:{'Content-Type':file.type||'application/octet-stream','X-PA-Filename':encodeURIComponent(file.name),...(state.auth?.csrf_token?{'X-CSRF-Token':state.auth.csrf_token}:{})},body:file});
      const payload=await response.json().catch(()=>({}));if(!response.ok)throw new Error(payload.error||'Не удалось загрузить файл');
      state.pendingFiles.push(payload.artifact);state.pendingFiles=state.pendingFiles.slice(-12);renderPendingFiles();toast(`${file.name}: файл проверен`,'success');
    }catch(error){toast(`${file.name}: ${error.message}`,'error')}
  }
  setBanner(state.pendingFiles.length?'Файлы прикреплены. Задайте вопрос или отправьте их для анализа.':'');
  await loadArtifacts();
}
function openFilePicker(){$('#fileInput')?.click()}
function renderArtifactList(){
  const host=$('#artifactList');if(!host)return;host.replaceChildren();
  if(!state.artifacts.length){host.append(node('div','muted','В workspace пока нет файлов.'));return}
  for(const item of state.artifacts){
    const row=node('div','artifact-row');row.dataset.artifactId=item.artifact_id;row.append(node('div','artifact-kind',String(item.format||'file').toUpperCase()));
    const copy=node('div','artifact-copy');copy.append(node('strong','',item.name),node('small','',`v${item.version} · ${prettySize(item.size)} · ${item.validation_status}`));
    const actions=node('div','artifact-actions');const attach=node('button','','В чат');attach.type='button';attach.onclick=()=>{if(!state.pendingFiles.some(x=>x.artifact_id===item.artifact_id))state.pendingFiles.push(item);renderPendingFiles();closeSettings();input.focus();toast('Файл прикреплён','success')};
    const download=node('a','','Скачать');download.href=item.download_url;download.target='_blank';download.rel='noopener';
    const remove=node('button','','Удалить');remove.type='button';remove.onclick=async()=>{if(!await confirmAction('Удалить файл?',`«${item.name}» будет удалён из workspace.`,'Удалить','danger'))return;try{await api(`/api/files/${item.artifact_id}`,{method:'DELETE'});state.pendingFiles=state.pendingFiles.filter(x=>x.artifact_id!==item.artifact_id);renderPendingFiles();await loadArtifacts();toast('Файл удалён','success')}catch(error){toast(error.message,'error')}};
    actions.append(attach,download,remove);row.append(copy,actions);host.append(row);
  }
}
async function loadArtifacts(){try{const result=await api('/api/files');state.artifacts=result.artifacts||[];renderArtifactList()}catch(_){state.artifacts=[];renderArtifactList()}}
async function createArtifactFromUi(){
  const fmt=$('#artifactFormat').value;let name=$('#artifactName').value.trim()||`document.${fmt}`;if(!name.toLowerCase().endsWith(`.${fmt}`))name=`${name.replace(/\.[^.]+$/,'')}.${fmt}`;
  let content=$('#artifactContent').value;if(fmt==='json'){try{content=JSON.parse(content)}catch(_){toast('Для JSON введите корректный JSON','error');return}}
  if(fmt==='csv'){content={rows:content.split(/\r?\n/).filter(Boolean).map(line=>line.split(',').map(cell=>cell.trim()))}}
  try{const result=await api('/api/files/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({format:fmt,name,content})});state.pendingFiles.push(result.artifact);renderPendingFiles();await loadArtifacts();toast(`${result.artifact.name}: создан и проверен`,'success')}catch(error){toast(error.message,'error')}
}
function renderMessageActions(message,index){
  const actions=node('div','message-actions');
  const copy=node('button','message-action','Копировать');copy.type='button';copy.onclick=()=>copyText(message.content,copy);actions.append(copy);
  if(message.role==='assistant'&&message.kind!=='capability'){
    const regenerate=node('button','message-action','Повторить');regenerate.type='button';regenerate.onclick=()=>regenerateAt(index);actions.append(regenerate);
  }
  return actions;
}
function renderChat(){
  chat.replaceChildren();
  const conversation=current();
  $('#conversationTitle').textContent=conversation?.title||'Новый чат';
  if(!conversation||conversation.messages.length===0){renderWelcome();return}
  conversation.messages.forEach((message,index)=>{
    const row=node('article',`message-row ${message.role}${message.kind==='capability'?' capability-message':''}`);
    row.dataset.messageId=message.id;
    const avatar=node('div','avatar',message.role==='user'?'':'PA');
    const body=node('div','message-body');
    if(message.role!=='user')body.append(node('div','message-author','Personal Agent Rus'));
    const bubble=node('div',`msg ${message.role}`);
    if(message.role==='assistant')renderRichText(bubble,message.content);else bubble.textContent=message.content;
    body.append(bubble);const attachments=renderMessageAttachments(message);if(attachments)body.append(attachments);const sources=renderSources(message);if(sources)body.append(sources);body.append(renderMessageActions(message,index));
    row.append(avatar,body);chat.appendChild(row);
  });
  requestAnimationFrame(()=>{document.scrollingElement?.scrollTo({top:document.scrollingElement.scrollHeight,behavior:'instant'})});
}
function entitlementEnabled(key){const item=state.auth?.entitlements?.features?.[key];return item?!!item.enabled:true}
function renderModes(){
  modes.replaceChildren();let defs=state.system?.modes||[];defs=defs.filter(mode=>entitlementEnabled(`mode_${mode.id}`));if(!defs.length)defs=(state.system?.modes||[]).filter(mode=>mode.id==='auto');
  if(!defs.some(item=>item.id===state.mode)){state.mode=defs[0]?.id||'auto';localStorage.setItem(MODE_KEY,state.mode)}
  const currentMode=defs.find(item=>item.id===state.mode)||defs[0];if(currentMode)$('#modeButton').firstChild.textContent=`${currentMode.label||currentMode.id} `;
  for(const mode of defs){const button=node('button',`mode${mode.id===state.mode?' active':''}`,mode.label||mode.id);button.type='button';button.dataset.mode=mode.id;button.title=mode.description||'';button.onclick=()=>{state.mode=mode.id;localStorage.setItem(MODE_KEY,mode.id);modes.hidden=true;$('#modeButton').setAttribute('aria-expanded','false');renderModes();toast(`Режим: ${mode.label||mode.id}`)};modes.appendChild(button)}
}
function renderCapabilities(){
  const host=$('#capabilitySettings');if(!host)return;host.replaceChildren();
  for(const [key,capability] of Object.entries(state.system?.capabilities||{})){
    const row=node('div','capability-setting');const feature=key==='files'?'files_read':key;const entitled=entitlementEnabled(feature);
    const copy=node('div','');copy.append(node('strong','',capability.label||key),node('span','',!entitled?'Недоступно на текущем тарифе':capability.status==='ready'?'Доступно в текущей сборке':'Подключается отдельным продуктовым слоем'));
    const badgeText=!entitled?'Тариф':capability.status==='ready'?'Готово':'Запланировано';row.append(copy,node('span',`capability-badge ${!entitled?'locked':capability.status||'planned'}`,badgeText));host.append(row);
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
  state.busy=busy;send.disabled=busy;input.disabled=busy;send.classList.toggle('working',busy);send.querySelector('span:first-child').textContent=busy?'Думаю…':'Отправить';
}
function setThinking(show){
  $('#thinkingRow')?.remove();
  if(!show)return;
  const row=node('article','message-row assistant thinking-row');row.id='thinkingRow';
  const avatar=node('div','avatar','PA');const body=node('div','message-body');body.append(node('div','message-author','Personal Agent Rus'));
  const dots=node('div','thinking-dots');dots.append(node('span'),node('span'),node('span'));body.append(dots);row.append(avatar,body);chat.append(row);requestAnimationFrame(()=>row.scrollIntoView({block:'end'}));
}

async function api(path,options){
  const opts={...(options||{})};const method=String(opts.method||'GET').toUpperCase();opts.headers={...(opts.headers||{})};
  if(!['GET','HEAD','OPTIONS'].includes(method)&&state.auth?.csrf_token)opts.headers['X-CSRF-Token']=state.auth.csrf_token;
  const response=await fetch(path,opts);let payload={};
  try{payload=await response.json()}catch(_){}
  if(!response.ok){const error=new Error(payload.error||'Ошибка запроса');error.status=response.status;error.code=payload.code;error.capability=payload.capability;throw error}
  return payload;
}
function semanticVersion(value){const match=String(value||'').match(/\d+\.\d+\.\d+/);return match?match[0]:null}
function enforceUiVersion(systemVersion){
  const backend=semanticVersion(systemVersion);const ui=semanticVersion(document.querySelector('meta[name="app-version"]')?.content||UI_VERSION);
  if(!backend||!ui||backend===ui)return true;
  const key=`par-ui-reloaded-${backend}`;
  if(sessionStorage.getItem(key)!=='1'){
    sessionStorage.setItem(key,'1');
    const url=new URL(location.href);url.searchParams.set('ui',backend);location.replace(url.toString());return false;
  }
  setBanner(`Интерфейс ${ui} не совпадает с Core ${backend}. Выполните REPAIR и обновите страницу.`,'warning');return true;
}
async function init(){
  loadStore();bindEvents();resizeInput();
  try{
    state.system=await api('/api/system');
    try{state.auth=await api('/api/auth/me')}catch(_){state.auth={ok:false,mode:state.system?.auth?.mode||'personal'}}
    if(!enforceUiVersion(state.system.version))return;
    $('#version').textContent=`v${state.system.version}`;$('#settingsVersion').textContent=`v${state.system.version}`;
    const account=$('#accountEntry');if(account){if(state.auth?.user){account.href='/account';account.querySelector('.account-label').textContent=state.auth.user.display_name||'Аккаунт'}else if(state.system?.auth?.mode==='accounts'){account.href='/login';account.querySelector('.account-label').textContent='Войти'}else{account.href='/account';account.querySelector('.account-label').textContent='Локальный профиль'}}
    const role=String(state.auth?.user?.role||'').toUpperCase();const roleAdmin=['OWNER','ADMIN'].includes(role);const personalOwner=state.system?.auth?.mode==='personal';$('#adminEntry').hidden=!roleAdmin;const adminSettings=$('#adminSettingsLink');if(adminSettings)adminSettings.hidden=!(roleAdmin||personalOwner);
    applySidebarPreferences();
    try{const scenarioPayload=await api('/api/scenarios');state.scenarios=scenarioPayload.scenarios||[]}catch(_){state.scenarios=[]}
    try{const prefPayload=await api('/api/preferences/web');state.webPreferences=prefPayload.preferences||null;renderWebPreferences()}catch(_){state.webPreferences=null}
    await loadServerStore();await loadArtifacts();await health();await maybeStartTour();
  }catch(error){setHealth(false,'Ошибка запуска');console.error(error)}
  requestAnimationFrame(()=>document.body.classList.add('ui-ready'));input.focus();
}
function linesToDomains(value){return String(value||'').split(/\r?\n|,/).map(x=>x.trim().toLowerCase()).filter(Boolean)}
function renderWebPreferences(){const p=state.webPreferences||{};if($('#webSearchScope'))$('#webSearchScope').value=p.search_scope||'internet';if($('#webRegion'))$('#webRegion').value=p.region||'';if($('#webAllowedDomains'))$('#webAllowedDomains').value=(p.allowed_domains||[]).join('\n');if($('#webExcludedDomains'))$('#webExcludedDomains').value=(p.excluded_domains||[]).join('\n');if($('#webPreferRussian'))$('#webPreferRussian').checked=p.prefer_russian!==false}
async function saveWebPreferences(){try{const payload=await api('/api/preferences/web',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({search_scope:$('#webSearchScope').value,region:$('#webRegion').value,allowed_domains:linesToDomains($('#webAllowedDomains').value),excluded_domains:linesToDomains($('#webExcludedDomains').value),prefer_russian:$('#webPreferRussian').checked})});state.webPreferences=payload.preferences;renderWebPreferences();toast('Настройки поиска сохранены','success')}catch(error){toast(error.message,'error')}}
async function health(){try{const result=await api('/api/health');setHealth(Boolean(result.ready),result.ready?'Готов':'Запускается')}catch(_){setHealth(false,'Нет связи')}}
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
  const lines=[`# ${c.title}`,'',`Экспорт Personal Agent Rus · ${new Date().toLocaleString('ru-RU')}`,''];
  for(const message of c.messages){
    lines.push(`## ${message.role==='user'?'Вы':'Personal Agent Rus'}`,'',message.content,'');
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
async function promptAction(title,message,value,inputLabel='Название диалога'){const result=await openActionModal({title,message,confirmText:'Сохранить',inputValue:value,inputLabel});return result===false?null:String(result||'').trim()}
async function selectAction(title,message,options,value=''){const result=await openActionModal({title,message,confirmText:'Переместить',selectOptions:options,selectValue:value});return result===false?null:String(result)}

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
  const labels={created:'Создано',planning:'Планирую',web:'Ищу источники',analysis:'Анализирую',artifacts:'Создаю файлы',verification:'Проверяю результат',completed:'Готово',failed:'Ошибка',cancelled:'Отменено'};
  return labels[task?.phase]||task?.phase||task?.status||'Задача';
}
function renderTaskList(){
  const host=$('#taskList');if(!host)return;host.replaceChildren();
  if(!state.tasks.length){host.append(node('div','muted','Задач пока нет.'));return}
  for(const task of state.tasks){const row=node('div','task-row');const copy=node('div','task-copy');copy.append(node('strong','',task.title||task.task_type),node('small','',`${task.status} · ${task.progress||0}% · ${taskPhaseLabel(task)}`));const actions=node('div','task-actions');if(!['COMPLETED','FAILED','CANCELLED','PARTIAL','BLOCKED'].includes(task.status)){const cancel=node('button','danger-button','Отменить');cancel.type='button';cancel.onclick=()=>cancelTask(task.id);actions.append(cancel)}row.append(copy,actions);host.append(row)}
}
async function loadTasks(){try{const result=await api('/api/tasks?limit=50');state.tasks=result.tasks||[];renderTaskList()}catch(_){state.tasks=[];renderTaskList()}}
async function cancelTask(taskId){try{await api(`/api/tasks/${taskId}/cancel`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});toast('Отмена запрошена','success');await loadTasks()}catch(error){toast(error.message,'error')}}
function updateTaskMessage(message,task){
  message.taskId=task.id;message.kind='task';message.content=`${taskPhaseLabel(task)} · ${task.progress||0}%`;
  if(task.status==='FAILED')message.content=`Задача завершилась ошибкой: ${task.error||'неизвестная ошибка'}`;
  if(task.status==='CANCELLED')message.content='Задача отменена.';
  if(task.status==='COMPLETED'){
    message.content=task.result?.answer||'Готово. Результаты проверены.';
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
  try{const payload=await api('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'research_report',question:content,formats:['md','xlsx','pdf']})});updateTaskMessage(progress,payload.task);saveStore();renderAll();pollTask(payload.task.id,progress);setBanner('Задача выполняется сервером: можно обновить страницу и вернуться позже.','info')}catch(error){progress.content=`Не удалось создать задачу: ${error.message}`;progress.kind='error';saveStore();renderAll();state.taskMode=null}finally{setBusy(false);input.value='';resizeInput();input.focus()}
}
function toggleToolTray(force){const tray=$('#toolTray');const nextHidden=force===undefined?!tray.hidden:!force;tray.hidden=nextHidden;$('#attachBtn').setAttribute('aria-expanded',String(!nextHidden))}

async function renameCurrent(){const c=current();if(!c)return;const value=await promptAction('Переименовать диалог','Название сохранится в Personal Agent и будет доступно после перезапуска.',c.title);if(value===null)return;const result=await api(`/api/conversations/${c.id}/rename`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:value||'Новый чат'})});const index=state.conversations.findIndex(x=>x.id===c.id);state.conversations[index]=serverConversation(result.conversation);renderAll();toast('Диалог переименован','success')}
async function clearCurrent(){const c=current();if(!c||!c.messages.length){toast('Диалог уже пуст');return}if(await confirmAction('Очистить сообщения?','Название диалога будет сброшено, сообщения удалятся с сервера.','Очистить','danger')){await clearCurrentNow();toast('Сообщения очищены','success')}}
async function deleteCurrent(){const c=current();if(!c)return;if(await confirmAction('Удалить диалог?',`«${c.title}» будет удалён из вашей истории.`,'Удалить','danger')){await deleteConversationNow(c.id);toast('Диалог удалён','success')}}
async function clearAll(){if(await confirmAction('Удалить все диалоги?','Будет удалена вся история текущего пользователя. Файлы workspace не удаляются.','Удалить всё','danger')){await clearAllNow();toast('История очищена','success')}}
async function renameFolder(folder){const name=await promptAction('Переименовать проект','Новое название будет сохранено для всех ваших устройств.',folder.name,'Название проекта');if(name===null||!name)return;const result=await api(`/api/folders/${folder.id}/rename`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});const index=state.folders.findIndex(x=>x.id===folder.id);if(index>=0)state.folders[index]=result.folder;renderAll();toast('Проект переименован','success')}
async function deleteFolder(folder){if(!await confirmAction('Удалить проект?',`Диалоги из «${folder.name}» останутся в истории без проекта.`,'Удалить проект','danger'))return;await api(`/api/folders/${folder.id}`,{method:'DELETE'});if(state.activeFolderId===folder.id)state.activeFolderId=null;await loadServerStore(state.search);toast('Проект удалён, диалоги сохранены','success')}
async function setConversationPinned(conversation,pinned){const result=await api(`/api/conversations/${conversation.id}/pin`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pinned})});const index=state.conversations.findIndex(x=>x.id===conversation.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);saveStore();renderAll();toast(pinned?'Диалог закреплён':'Диалог откреплён','success')}
async function moveCurrent(){const c=current();if(!c)return;const options=[{value:'',label:'Без проекта'},...state.folders.map(folder=>({value:folder.id,label:folder.name}))];const folderId=await selectAction('Переместить диалог','Выберите проект для текущего диалога.',options,c.folder_id||'');if(folderId===null)return;const result=await api(`/api/conversations/${c.id}/move`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({folder_id:folderId||null})});const index=state.conversations.findIndex(x=>x.id===c.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);await loadServerStore(state.search);toast(folderId?'Диалог перемещён в проект':'Диалог перемещён в «Все чаты»','success')}
async function archiveCurrent(){const c=current();if(!c)return;const archived=!Boolean(c.archived_at);const result=await api(`/api/conversations/${c.id}/archive`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({archived})});const index=state.conversations.findIndex(x=>x.id===c.id);if(index>=0)state.conversations[index]=serverConversation(result.conversation);if(archived&&state.activeFolderId!=='__archived__'){const next=state.conversations.find(x=>!x.archived_at&&x.id!==c.id);state.activeId=next?.id||null;if(!state.activeId)await newConversation(false)}await loadServerStore(state.search);toast(archived?'Диалог перемещён в архив':'Диалог возвращён из архива','success')}
async function createFolder(){const name=await promptAction('Новый проект','Проекты помогают группировать связанные диалоги.','Новый проект','Название проекта');if(name===null||!String(name).trim())return;const result=await api('/api/folders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});state.folders.push(result.folder);state.activeFolderId=result.folder.id;saveStore();renderAll();toast('Проект создан','success')}
async function sendRequest({addUser=true,text=null}={}){
  if(state.busy)return;
  let content=String(text??input.value).trim();if(addUser&&!content&&state.pendingFiles.length)content='Проанализируй приложенные файлы и выдели главное.';if(addUser&&!content)return;
  setBanner('');
  if(addUser&&state.taskMode==='research_report'){await sendTaskRequest(content);return}
  if(addUser){const attachments=[...state.pendingFiles];addMessage({role:'user',content,attachments});state.pendingFiles=[];renderPendingFiles();input.value='';resizeInput()}
  setBusy(true);setThinking(true);
  const pendingIntent=state.intentHint;
  if(pendingIntent==='research')setBanner('Исследую: ищу источники → читаю страницы → сверяю факты → формирую вывод…','info');
  else if(pendingIntent==='search'||/https?:\/\//i.test(content))setBanner('Ищу и читаю веб-источники. Ответ появится после синтеза фактов…','info');
  try{
    const c=current();
    const history=c.messages.filter(message=>!String(message.kind||'').startsWith('capability')).map(({role,content})=>({role,content}));
    const fileIds=[...new Set(c.messages.flatMap(message=>(message.attachments||[]).map(item=>item.artifact_id)).filter(Boolean))].slice(-12);
    const result=await api('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:state.mode,preset:state.preset,intent_hint:state.intentHint,scenario_id:state.scenarioId||'',file_ids:fileIds,messages:history,conversation_id:c.id,persist_user:addUser,attachments:addUser?(c.messages.at(-1)?.attachments||[]):[]})});
    addMessage({...result.message,sources:result.sources||[]});if(result.intent!=='clarification')state.scenarioId=null;else if(result.scenario?.id)state.scenarioId=result.scenario.id;state.intentHint='auto';setBanner(result.intent==='clarification'?'Нужно одно короткое уточнение — после ответа Personal Agent продолжит задачу.':'');try{await loadServerStore(state.search)}catch(_){}if((result.sources||[]).length)toast(`Ответ собран по ${result.sources.length} веб-источникам`,'success');
  }catch(error){
    if(error.code==='capability_unavailable'){
      const c=current();const last=[...(c?.messages||[])].reverse().find(message=>message.role==='user'&&message.kind==='message');if(last)last.kind='capability-request';saveStore();
      addMessage({role:'assistant',content:error.message||'Для этого запроса нужна возможность, которая пока не подключена.',kind:'capability'});
      setBanner('Запрос остановлен до обращения к локальной модели: требуется отдельная capability.','warning');
    }else{
      addMessage({role:'assistant',content:`Не удалось получить ответ: ${error.message}`,kind:'error'});setBanner('Ответ не получен. Можно повторить запрос после восстановления runtime.','warning');
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
  c.messages.splice(assistantIndex,1);c.updatedAt=now();saveStore();renderAll();toast('Повторяю последний ответ');await sendRequest({addUser:false,text:c.messages[userIndex].content});
}

const TOUR_STEPS=[
  {selector:'#brandHelp',title:'Добро пожаловать в Personal Agent',text:'Здесь можно пройти обучение заново, открыть руководство и быстро посмотреть возможности продукта.'},
  {selector:'#newChat',title:'Новый чат',text:'Создайте отдельный диалог. Быстрая клавиша — Ctrl+N.'},
  {selector:'#input',title:'Просто напишите задачу',text:'Опишите результат обычным языком. Personal Agent сам выберет нужные возможности.'},
  {selector:'#attachBtn',title:'Файлы и инструменты',text:'Прикрепляйте документы или включайте Web, Code и длинные задачи.'},
  {selector:'#chatSearch',title:'История и поиск',text:'Диалоги теперь хранятся на сервере и находятся по заголовку и содержимому.'},
  {selector:'#newFolder',title:'Проекты',text:'Группируйте связанные диалоги в проекты. Новый чат создаётся в выбранном проекте.'},
  {selector:'#exportChatButton',title:'Результат можно забрать',text:'Скачивайте текущий чат как проверенный Markdown-артефакт.'},
  {selector:'#privacyPill',title:'Приватность понятна сразу',text:'Локальный режим означает, что базовая обработка идёт на вашем компьютере. Remote-переходы должны быть явными.'},
  {selector:'#accountEntry',title:'Профиль и тариф',text:'Здесь находятся аккаунт, подписка, использование и пользовательские настройки.'}
];
let tourIndex=0;
function applySidebarPreferences(){const width=Math.max(240,Math.min(420,Number(localStorage.getItem('par-sidebar-width')||282)));document.documentElement.style.setProperty('--sidebar-user',`${width}px`);const collapsed=localStorage.getItem('par-sidebar-collapsed')==='1';$('#sidebar').classList.toggle('collapsed',collapsed);if(collapsed)document.documentElement.style.setProperty('--sidebar-user','68px')}
function setSidebarCollapsed(value){localStorage.setItem('par-sidebar-collapsed',value?'1':'0');applySidebarPreferences();$('#collapseSidebar').textContent=value?'›':'‹'}
function bindSidebarResize(){const handle=$('#sidebarResizer');let active=false;handle.addEventListener('pointerdown',event=>{active=true;handle.classList.add('dragging');handle.setPointerCapture(event.pointerId)});handle.addEventListener('pointermove',event=>{if(!active)return;const width=Math.max(240,Math.min(420,event.clientX));document.documentElement.style.setProperty('--sidebar-user',`${width}px`);localStorage.setItem('par-sidebar-width',String(width))});const stop=()=>{active=false;handle.classList.remove('dragging')};handle.addEventListener('pointerup',stop);handle.addEventListener('pointercancel',stop)}
function openHelp(){closeSidebar();$('#helpBackdrop').hidden=false}
function closeHelp(){ $('#helpBackdrop').hidden=true }
function renderHelpCapabilities(){const host=$('#helpCapabilities');host.replaceChildren();for(const [key,item] of Object.entries(state.system?.capabilities||{})){const row=node('div','help-capability');row.append(node('span','',item.status==='ready'?'✓':'○'));const copy=node('div','');copy.append(node('strong','',item.label||key),node('small','',item.status==='ready'?'Доступно сейчас':item.status==='degraded'?'Ограниченно доступно':'Подключается следующим слоем'));row.append(copy);host.append(row)}host.hidden=false}
function tourTarget(){return document.querySelector(TOUR_STEPS[tourIndex]?.selector||'')}
function positionTour(){const target=tourTarget();if(!target)return;target.scrollIntoView({block:'center',inline:'nearest'});requestAnimationFrame(()=>{const rect=target.getBoundingClientRect();const pad=7;const spot=$('#tourSpotlight');Object.assign(spot.style,{left:`${Math.max(4,rect.left-pad)}px`,top:`${Math.max(4,rect.top-pad)}px`,width:`${Math.max(24,rect.width+pad*2)}px`,height:`${Math.max(24,rect.height+pad*2)}px`});const card=$('#tourCard');const w=Math.min(360,window.innerWidth-28);let left=rect.right+18;if(left+w>window.innerWidth-14)left=Math.max(14,rect.left-w-18);let top=Math.max(14,Math.min(window.innerHeight-230,rect.top));if(window.innerWidth<720){left=14;top=Math.max(14,window.innerHeight-250)}Object.assign(card.style,{left:`${left}px`,top:`${top}px`})})}
async function persistTour(status){try{await api('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona:'user',status,current_step:tourIndex})})}catch(_){}}
function renderTour(){const step=TOUR_STEPS[tourIndex];if(!step)return;$('#tourProgress').textContent=`${tourIndex+1} из ${TOUR_STEPS.length}`;$('#tourTitle').textContent=step.title;$('#tourText').textContent=step.text;$('#tourBack').disabled=tourIndex===0;$('#tourNext').textContent=tourIndex===TOUR_STEPS.length-1?'Готово':'Далее';positionTour()}
async function startTour(force=false){closeHelp();if(!force){try{const value=await api('/api/onboarding');if(['completed','skipped'].includes(value.state?.status))return}catch(_){}}tourIndex=0;$('#tourLayer').hidden=false;await persistTour('in_progress');renderTour()}
async function finishTour(status='completed'){await persistTour(status);$('#tourLayer').hidden=true;input.focus()}
async function maybeStartTour(){await startTour(false)}

function bindEvents(){
  $('#newChat').onclick=()=>newConversation(true);$('#newFolder').onclick=createFolder;$('#brandHelp').onclick=openHelp;$('#helpEntry').onclick=openHelp;$('#closeHelp').onclick=closeHelp;$('#helpBackdrop').onclick=e=>{if(e.target===$('#helpBackdrop'))closeHelp()};$('#restartTour').onclick=()=>startTour(true);$('#showCapabilities').onclick=renderHelpCapabilities;$('#collapseSidebar').onclick=()=>setSidebarCollapsed(!$('#sidebar').classList.contains('collapsed'));bindSidebarResize();$('#openSidebar').onclick=openSidebar;$('#closeSidebar').onclick=closeSidebar;$('#sidebarBackdrop').onclick=closeSidebar;
  let searchTimer;$('#chatSearch').addEventListener('input',event=>{state.search=event.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadServerStore(state.search).catch(error=>toast(error.message,'warning')),180)});
  $('#clearAllShortcut').onclick=clearAll;
  $('#filesEntry').onclick=()=>{openSettings('files');loadArtifacts()};$('#codeEntry').onclick=()=>{openSettings('code');refreshCodeStatus()};$('#tasksEntry').onclick=()=>{openSettings('tasks');loadTasks()};$('#settingsEntry').onclick=()=>openSettings('general');$('#closeSettings').onclick=closeSettings;$('#settingsBackdrop').onclick=event=>{if(event.target===$('#settingsBackdrop'))closeSettings()};
  $$('[data-settings-tab]').forEach(button=>button.onclick=()=>selectSettingsTab(button.dataset.settingsTab));
  $('#exportCurrentChat').onclick=exportCurrent;$('#exportAllChats').onclick=exportAll;$('#clearCurrentChat').onclick=clearCurrent;$('#clearAllChats').onclick=clearAll;
  $('#runCode').onclick=runCode;$('#cancelCode').onclick=cancelCode;$('#refreshTasks').onclick=loadTasks;
  $('#fileInput').onchange=async event=>{await uploadSelectedFiles(event.target.files);event.target.value=''};$('#uploadArtifact').onclick=openFilePicker;$('#createArtifact').onclick=createArtifactFromUi;$('#artifactFormat').onchange=event=>{const fmt=event.target.value;const field=$('#artifactName');field.value=(field.value||'document').replace(/\.[^.]+$/, '')+`.${fmt}`};
  $('#exportChatButton').onclick=exportCurrent;$('#chatMenuButton').onclick=event=>{event.stopPropagation();toggleChatMenu()};
  $('#chatMenu').onclick=event=>{const item=event.target.closest('[data-action]');if(!item)return;toggleChatMenu(false);const action=item.dataset.action;if(action==='rename')renameCurrent();else if(action==='pin'){const c=current();if(c)setConversationPinned(c,!c.pinned_at)}else if(action==='move')moveCurrent();else if(action==='archive')archiveCurrent();else if(action==='export')exportCurrent();else if(action==='clear')clearCurrent();else if(action==='delete')deleteCurrent()};
  if($('#saveWebPreferences'))$('#saveWebPreferences').onclick=saveWebPreferences;$('#attachBtn').onclick=event=>{event.stopPropagation();toggleToolTray()};$('#modeButton').onclick=event=>{event.stopPropagation();modes.hidden=!modes.hidden;$('#modeButton').setAttribute('aria-expanded',String(!modes.hidden))};
  $('#toolTray').onclick=event=>{const tool=event.target.closest('[data-tool]');if(!tool)return;toggleToolTray(false);const id=tool.dataset.tool;if(id==='web'){state.intentHint='search';setBanner('Веб включён для следующего запроса: поиск, чтение сайтов и источники.','info');input.focus();return}if(id==='files'){openFilePicker();return}if(id==='code'){openSettings('code');refreshCodeStatus();return}if(id==='task-report'){state.taskMode='research_report';setBanner('Следующий запрос станет задачей: источники → анализ → MD/XLSX/PDF → проверка.','info');input.focus();return}setBanner(`${tool.querySelector('strong')?.textContent||'Эта возможность'} пока не подключена. Кнопка показана как честный preview будущей capability.`,'info')};
  $('#actionCancel').onclick=()=>closeActionModal(false);$('#actionConfirm').onclick=()=>{const field=$('#actionInput'),select=$('#actionSelect');closeActionModal(!field.hidden?field.value:(!select.hidden?select.value:true))};$('#actionBackdrop').onclick=event=>{if(event.target===$('#actionBackdrop'))closeActionModal(false)};
  $('#actionInput').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('#actionConfirm').click()}});
  input.addEventListener('input',resizeInput);input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('#form').requestSubmit()}});
  $('#form').onsubmit=event=>{event.preventDefault();sendRequest()};
  document.addEventListener('click',event=>{if(!event.target.closest('.menu-wrap'))toggleChatMenu(false);if(!event.target.closest('#toolTray')&&!event.target.closest('#attachBtn'))toggleToolTray(false);if(!event.target.closest('.composer-mode-wrap')){modes.hidden=true;$('#modeButton').setAttribute('aria-expanded','false')}});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'){if(!$('#tourLayer').hidden){finishTour('skipped');return}toggleChatMenu(false);toggleToolTray(false);closeHelp();if(!$('#actionBackdrop').hidden)closeActionModal(false);else if(!$('#settingsBackdrop').hidden)closeSettings();else closeSidebar()}
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='n'){event.preventDefault();newConversation(true)}else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();$('#chatSearch').focus()}else if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='b'){event.preventDefault();setSidebarCollapsed(!$('#sidebar').classList.contains('collapsed'))}
  });
  $('#tourSkip').onclick=()=>finishTour('skipped');$('#tourBack').onclick=()=>{if(tourIndex>0){tourIndex--;persistTour('in_progress');renderTour()}};$('#tourNext').onclick=()=>{if(tourIndex>=TOUR_STEPS.length-1){finishTour('completed')}else{tourIndex++;persistTour('in_progress');renderTour()}};window.addEventListener('resize',()=>{if(!$('#tourLayer').hidden)positionTour()});
}

init();
setInterval(health,15000);
