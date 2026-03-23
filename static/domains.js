// Delegator stub: load the real domains JS from /static/js/
(function(){
  var s = document.createElement('script');
  s.src = '/static/js/domains.js';
  s.defer = true;
  document.head.appendChild(s);
})();
