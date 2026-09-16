"use strict";
const demoForm = document.querySelector("#demoForm");
const demoSend = document.querySelector("#demoSend");
const demoStatus = document.querySelector("#demoStatus");
let demoRemaining = 0;
function updateDemoRemaining(value) {
  demoRemaining = value;
  document.querySelector("#demoRemaining").textContent = `Осталось запросов: ${value} из 2`;
  demoSend.disabled = value <= 0;
}
async function loadDemo() {
  demoSend.disabled = true;
  try {
    const response = await fetch("/api/demo/chat");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    updateDemoRemaining(data.remaining);
  } catch (error) {
    demoStatus.textContent = error.message || "Не удалось загрузить демонстрацию. Обновите страницу.";
  }
}
for (const button of document.querySelectorAll("#demoExamples button")) {
  button.onclick = () => { document.querySelector("#demoMessage").value = button.textContent; document.querySelector("#demoMessage").focus(); };
}
demoForm.onsubmit = async (event) => {
  event.preventDefault();
  if (demoSend.disabled) return;
  demoSend.disabled = true;
  demoStatus.textContent = "Готовлю ответ…";
  try {
    const response = await fetch("/api/demo/chat", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message: document.querySelector("#demoMessage").value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Не удалось получить ответ");
    const answer = document.querySelector("#demoAnswer");
    answer.textContent = data.answer;
    answer.hidden = false;
    updateDemoRemaining(data.remaining);
    demoStatus.textContent = data.remaining ? "Ответ готов. Можно задать ещё один вопрос." : "Демо завершено. Создайте бесплатный аккаунт, чтобы продолжить.";
  } catch (error) {
    demoStatus.textContent = error.message;
    await loadDemo();
  } finally {
    demoSend.disabled = demoRemaining <= 0;
  }
};
loadDemo();
