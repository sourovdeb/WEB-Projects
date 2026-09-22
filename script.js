const buttons=[...document.querySelectorAll('.filter')];
const projects=[...document.querySelectorAll('.project')];
buttons.forEach(button=>button.addEventListener('click',()=>{
  const filter=button.dataset.filter;
  buttons.forEach(item=>{item.classList.toggle('active',item===button);item.setAttribute('aria-pressed',String(item===button))});
  projects.forEach(project=>{project.hidden=filter!=='all'&&project.dataset.category!==filter});
}));
document.getElementById('year').textContent=new Date().getFullYear();
