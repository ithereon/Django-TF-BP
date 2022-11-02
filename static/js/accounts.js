Dropzone.autoDiscover = false;

function getModal(el) {
    return new bootstrap.Modal($(el)[0])
}

function initDropzoneFor($el) {
    $el.find('[data-dropzone]').each(function() {
        $(this).click(function(ev){ ev.stopPropagation() });
        var dz = new Dropzone($(this)[0], {
            previewTemplate: document.querySelector('#dz-template').innerHTML,
            maxFiles: 1,
            maxFilesize: 2,
            acceptedFiles: '.pdf, .docx,',
            autoProcessQueue: false
        });
    
        dz.on("addedfile", function(file) {
            $('#docModal').data('dropzone-target', dz);
            getModal('#docModal').show();
        });
    
        dz.on("complete", function(file) {
            window.location.reload();
        });
    });
    
    $el.find('[data-dropzone-client]').each(function() {
        $(this).click(function(ev){ ev.stopPropagation() });
        var dz = new Dropzone($(this)[0], {
            previewTemplate: document.querySelector('#dz-template').innerHTML,
            maxFiles: 1,
            maxFilesize: 2,
            acceptedFiles: '.pdf, .docx,',
            autoProcessQueue: true
        });
    
        dz.on("complete", function(file) {
            window.location.reload();
        });
    });

    
    $el.find('[data-dz-remove]').click(function(e) {
        e.preventDefault();
        var c = confirm('are you sure you want to delete file?');
        if (c) {
            var $dz = $(this).closest('.dropzone');
            var json = readDocProperties($dz);
            var href = $(e.target).closest('a').attr('href');
            window.location.href = href;
        }
        return false;
    });
}

var pageready = false;
$(document).ready(function(){
    if(pageready) return; pageready = true;
    initDropzoneFor($('body'));
    $(".page-alert").fadeTo(4000, 500).slideUp(500, function(){
        $(".page-alert").slideUp(500);
    });
});

function submitDocName() {
    $modal = $('#docModal');
    var docName = $modal.find('#docName').val();
    var dz = $modal.data('dropzone-target');
    $(dz.element).find('[name="name"]').val(docName);
    dz.processQueue();
    getModal(modal[0]).hide();
    return false;
}

function hideDocName() {
    $modal = $('#docModal');
    var dz = $modal.data('dropzone-target');
    dz.removeAllFiles();
    getModal(modal[0]).hide();
    return false;
}

function readDocProperties($dz) {
    var docId = $dz.attr('data-doc-id');
    var docName = $dz.attr('data-doc-name');
    var clientId = $dz.attr('data-client-id');
    var caseId = $dz.attr('data-case-id');
    var noteId = $dz.attr('data-note-id');
    var json = { docId, clientId, caseId, noteId, docName };
    return json;
}

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