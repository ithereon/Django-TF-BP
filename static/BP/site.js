
function debounce(func, wait, immediate) {
    var timeout;
  
    return function executedFunction() {
      var context = this; var args = arguments;
          
      var later = function() {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
  
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
}

function readForm(el){
    var $form = $(el);
    var data = {}; $form.find('[name]').each(function(i, p) { data[$(p).attr('name')] = $(p).val() });
    return data;
}