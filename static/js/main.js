Dropzone.autoDiscover = false;

function initDropzoneFor($el) {
    $el.find('[data-dropzone]').each(function () {
        $(this).click(function (ev) { ev.stopPropagation() });
        var dz = new Dropzone($(this)[0], {
            previewTemplate: document.querySelector('#dz-template').innerHTML,
            maxFiles: 1,
            maxFilesize: 2,
            acceptedFiles: '.pdf, .docx,',
            autoProcessQueue: false
        });

        dz.on("addedfile", function (file) {
            $('#docModal').data('dropzone-target', dz);
            $('#docModal').modal();
        });

        dz.on("complete", function (file) {
            window.location.reload();
        });
    });

    $el.find('[data-dropzone-client]').each(function () {
        $(this).click(function (ev) { ev.stopPropagation() });
        var dz = new Dropzone($(this)[0], {
            previewTemplate: document.querySelector('#dz-template').innerHTML,
            maxFiles: 1,
            maxFilesize: 2,
            acceptedFiles: '.pdf, .docx,',
            autoProcessQueue: true
        });

        dz.on("complete", function (file) {
            window.location.reload();
        });
    });


    $el.find('[data-dz-remove]').click(function (e) {
        e.preventDefault();
        var c = confirm('are you sure you want to delete file?');
        if (c) {
            var href = $(e.target).closest('a').attr('href');
            window.location.href = href;
        }
        return false;
    });
}

initDropzoneFor($('body'));

function submitDocName() {
    $modal = $('#docModal');
    var docName = $modal.find('#docName').val();
    var dz = $modal.data('dropzone-target');
    $(dz.element).find('[name="name"]').val(docName);
    dz.processQueue();
    $modal.modal('hide');
    return false;
}

function hideDocName() {
    $modal = $('#docModal');
    var dz = $modal.data('dropzone-target');
    dz.removeAllFiles();
    $modal.modal('hide');
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

function showRightSidebar() {
    $('.sidebar-right').removeClass('visible');
    $('.sidebar-right').addClass('visible');
}

function hideRightSidebar() {
    $('.sidebar-right').removeClass('visible');
}

$('[data-close="sidebar-right"]').click(function () {
    hideRightSidebar();
});

function previewDocInSidebar(el, ev) {
    ev.preventDefault();
    ev.stopPropagation();

    var $dz = $(el);
    var json = readDocProperties($dz);
    var html = $('#doc-preview-template').html();
    var template = Handlebars.compile(html);
    $('.sidebar-right').html(template(json));
    showRightSidebar();
}

function showPdfContainer($tab) {
    $tab.find('.pdfcontainer').removeClass('visible');
    $tab.find('.pdfcontainer').addClass('visible');
}

function hidePdfContainer($tab) {
    $tab.find('.pdfcontainer').removeClass('visible');
}

function toggleDocPreview(el, ev) {
    ev.preventDefault();
    ev.stopPropagation();

    var $dz = $(el);
    var json = readDocProperties($dz);
    var $tab = $dz.closest('.custom-tab');
    var $pdfViewer = $tab.find(".pdfViewer");

    var oldId = $pdfViewer.data("docId");
    var newId = json.docId;
    $dz.closest('.d-flex').find('.dz-xs').removeClass("active");

    if (oldId == newId) {
        $pdfViewer.data("docId", null);
        hidePdfContainer($tab);
    }
    else {
        $pdfViewer.data("docId", newId);
        showPdfContainer($tab);
        $dz.addClass("active");

        var el = $pdfViewer.data("kendoPDFViewer");
        if (el) el.destroy();
        $pdfViewer.empty();

        setTimeout(function () {
            $pdfViewer.kendoPDFViewer({
                toolbar: {
                    items: ["pager", "spacer", "zoom", "toggleSelection", "spacer", "search", "download", "print", {
                        name: "delete",
                        template: `<a href="/BP/deleteDocument/${json.clientId}/${json.caseId}/${json.docId}/" 
                        class="k-button k-button-md k-rounded-md k-button-flat k-button-flat-base k-icon-button">
                            <i class="fa fa-trash text-danger" onclick="onPdfDelete(event)"/>
                        </div>`
                    }]
                },
                pdfjsProcessing: {
                    file: `/BP/open/${json.docId}/`
                },
                width: "100%",
                height: 600
            });
        }, 1000);
    }
}

function onPdfDelete(e) {
    e.preventDefault();
    var c = confirm('are you sure you want to delete file?');
    if (c) {
        var href = $(e.target).closest('a').attr('href');
        window.location.href = href;
    }
    return false;
}


const onMenuRouteHover = (item) => {
    var blue = item.getElementsByClassName('blueSpace')[0]
    blue.style.backgroundColor = '#fff'
    item.style.backgroundColor = '#fff'
}

const onMenuRouteLeave = (item) => {
    var blue = item.getElementsByClassName('blueSpace')[0]
    blue.style.background = '#093761'
    item.style.background = '#fff'    
}

