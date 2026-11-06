const form = document.querySelector('#task-form');
const titleInput = document.querySelector('#title');
const descriptionInput = document.querySelector('#description');
const completedInput = document.querySelector('#completed');
const save = document.querySelector('#save');
const cancel = document.querySelector('#cancel');
let editingId = null;

function message(text, error = false) {
  const element = document.querySelector('#message');
  element.textContent = text;
  element.classList.toggle('error', error);
}

async function api(path = '', options = {}) {
  const response = await fetch(`/api/tasks${path}`, {
    ...options, headers: { 'Content-Type': 'application/json' },
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Unable to save changes.');
  return body;
}

function resetForm() {
  editingId = null;
  form.reset();
  document.querySelector('#form-heading').textContent = 'New task';
  save.textContent = 'Create task';
  cancel.hidden = true;
}

function editTask(task) {
  editingId = task.id;
  titleInput.value = task.title;
  descriptionInput.value = task.description;
  completedInput.checked = task.completed;
  document.querySelector('#form-heading').textContent = 'Edit task';
  save.textContent = 'Save changes';
  cancel.hidden = false;
  titleInput.focus();
}

async function loadTasks() {
  const tasks = await api();
  const list = document.querySelector('#tasks');
  list.replaceChildren();
  document.querySelector('#count').textContent = `${tasks.length} task${tasks.length === 1 ? '' : 's'}`;
  if (!tasks.length) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = 'A fresh start. Create your first task to get going.';
    list.append(empty);
  }
  for (const task of tasks) {
    const card = document.createElement('article');
    card.className = `task${task.completed ? ' done' : ''}`;
    const top = document.createElement('div');
    top.className = 'task-top';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = task.completed;
    checkbox.setAttribute('aria-label', `Mark ${task.title} ${task.completed ? 'incomplete' : 'complete'}`);
    checkbox.addEventListener('change', async () => {
      checkbox.disabled = true;
      try {
        await api(`/${task.id}`, { method: 'PUT', body: JSON.stringify({ title: task.title, description: task.description, completed: checkbox.checked }) });
        if (editingId === task.id) completedInput.checked = checkbox.checked;
        await loadTasks();
        message('Task updated.');
      } catch (error) { checkbox.checked = task.completed; message(error.message, true); }
      finally { checkbox.disabled = false; }
    });
    const heading = document.createElement('h3');
    heading.textContent = task.title;
    top.append(checkbox, heading);
    const description = document.createElement('p');
    description.textContent = task.description;
    const actions = document.createElement('div');
    actions.className = 'actions';
    const edit = document.createElement('button');
    edit.className = 'secondary';
    edit.textContent = 'Edit';
    edit.addEventListener('click', () => editTask(task));
    const remove = document.createElement('button');
    remove.className = 'danger';
    remove.textContent = 'Delete';
    remove.addEventListener('click', async () => {
      if (!confirm(`Delete “${task.title}”?`)) return;
      remove.disabled = true;
      try {
        await api(`/${task.id}`, { method: 'DELETE' });
        if (editingId === task.id) resetForm();
        await loadTasks();
        message('Task deleted.');
      } catch (error) { message(error.message, true); }
      finally { remove.disabled = false; }
    });
    actions.append(edit, remove);
    card.append(top, description, actions);
    list.append(card);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const isEditing = editingId !== null;
  save.disabled = true;
  cancel.disabled = true;
  try {
    await api(isEditing ? `/${editingId}` : '', {
      method: isEditing ? 'PUT' : 'POST',
      body: JSON.stringify({ title: titleInput.value, description: descriptionInput.value, completed: completedInput.checked }),
    });
    resetForm();
    await loadTasks();
    message(isEditing ? 'Task updated.' : 'Task created.');
  } catch (error) { message(error.message, true); }
  finally { save.disabled = false; cancel.disabled = false; }
});
cancel.addEventListener('click', resetForm);
loadTasks().catch(error => message(error.message, true));
