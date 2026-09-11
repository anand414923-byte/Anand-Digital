const header = document.querySelector('.site-header');
const menu = document.querySelector('.menu-button');
menu.addEventListener('click', () => {
  const open = header.classList.toggle('open');
  menu.setAttribute('aria-expanded', open);
  menu.textContent = open ? '×' : '☰';
});
document.querySelectorAll('nav a').forEach(link => link.addEventListener('click', () => {
  header.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); menu.textContent = '☰';
}));
document.getElementById('year').textContent = new Date().getFullYear();
