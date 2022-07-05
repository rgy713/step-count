var ajax_json = function(type, url, data, success, error, view_loading){
    if( view_loading ){
        $("#modal-loading").css("display","inherit");
    }
    $.ajax({
        url: url,
        dataType: 'json',
        type: type,
        data: data,
        success: function (data) {
            $("#modal-loading").css("display","none");
            if (data.type === 'success')
                success && success(data.content);
            else
                error && error(data.content);
        },
        error: function(data){
            window.location=window.location.href;
            $("#modal-loading").css("display","none");
            error && error(data);
        }
    });
};

var ajax_form = function(type, url, data, success, error, view_loading){

    $("#modal-loading").css("display","inherit");

    $.ajax({
        url: url,
        dataType: 'json',
        type: type,
        processData: false,
        contentType: false,
        data: data,
        success: function (data) {
            $("#modal-loading").css("display","none");
            if (data.type === 'success')
                success && success(data.content);
            else
                error && error(data.content);
        },
        error: function(data){
            window.location=window.location.href;
            $("#modal-loading").css("display","none");
            error && error(data);
        }
    });
};

$('a[data-toggle="sidebar"]').on('click', function(e){
    $(".dataTables_scrollHeadInner").css("width","100%");
    $(".dataTables_scrollHeadInner > table").css("width","100%");
   $($.fn.dataTable.tables(true)).DataTable()
      .responsive.recalc() .columns.adjust();
});