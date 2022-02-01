function fadePgpKeyToggle() {
  var key = document.getElementById('pgpkey');
  key.style.transition = "opacity 1s";
  if (key.style.opacity == 1) {
    key.style.opacity = "0";
  }
  else {
    key.style.opacity = "1";
  }
}
