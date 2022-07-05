$(function () {

    $(document).ready(function() {  

        // $('a[href^=#]').bind("click", jump);

        // if (location.hash){
        //     setTimeout(function(){
        //         $('html, body').scrollTop(0).show();
        //         jump();
        //     }, 0);
        // }else{
        //     $('html, body').show();
        // }

        // jQuery("#sample_editable_1_filter").css('display','none');

        jQuery(document).on("click", ".public-btn", function() {
            var id = $(this).parents('tr').children().first().text()
            var hitURL = baseURL + "admin_setstate";

            var pathname = window.location.pathname;
            if (pathname.indexOf("news") != -1) {
                hitURL += '/1';
            }
            else if (pathname.indexOf("notices")) {
                hitURL += '/2';
            }

            jQuery.ajax({
            type : "POST",
            dataType : "json",
            url : hitURL,
            data : { id : id, state: 2, } 
            }).done(function(data){
                if(data['status'] == 111) {
                    $(location).attr('href', baseURL + 'admin/news');
                }
                else {
                    $(location).attr('href', baseURL + 'admin/notices');
                }  
            });    
        });
        jQuery(document).on("click", ".private-btn", function() {
            var id = $(this).parents('tr').children().first().text()
            var hitURL = baseURL + "admin_setstate";

            var pathname = window.location.pathname;
            if (pathname.indexOf("news") != -1) {
                hitURL += '/1';
            }
            else if (pathname.indexOf("notices")) {
                hitURL += '/2';
            }

            jQuery.ajax({
            type : "POST",
            dataType : "json",
            url : hitURL,
            data : { id : id, state: 1, } 
            }).done(function(data){
                if(data['status'] == 111) {
                    $(location).attr('href', baseURL + 'admin/news');
                }
                else {
                    $(location).attr('href', baseURL + 'admin/notices');
                }
            });
        });
        jQuery(document).on("click", ".draft-btn", function() {
            var id = $(this).parents('tr').children().first().text()
            var hitURL = baseURL + "admin_setstate";

            var pathname = window.location.pathname;
            if (pathname.indexOf("news") != -1 ) {
                hitURL += '/1';
            }
            else if (pathname.indexOf("notices")) {
                hitURL += '/2';
            }

            jQuery.ajax({
            type : "POST",
            dataType : "json",
            url : hitURL,
            data : { id : id, state: 0, } 
            }).done(function(data){
                if(data['status'] == 111) {
                    $(location).attr('href', baseURL + 'admin/news');
                }
                else {
                    $(location).attr('href', baseURL + 'admin/notices');
                }
            });
        });
        $('.insert-news-btn').click(function() {
            var minute = $('#news-minute-type  option:selected').text();
            var hour = $('#news-hour-type  option:selected').text();
            
            var inputdate = hour + " " + minute;
            var inputcontent =$('#news-date-gap').val();
            if(inputcontent.length>200)
                return;
      
            var inputDate = $("<input>").attr("type", "hidden").attr("name", "inputdate").val(inputdate);
            var inputContent = $("<input>").attr("type", "hidden").attr("name", "inputcontent").val(inputcontent);
            $('.news-contents-form').append($(inputDate));
            $('.news-contents-form').append($(inputContent));
            $('.news-contents-form').submit();
        });

        if(window.location.pathname == "/list/news" || window.location.pathname == "/list/inquery" 
            ) {
            win_height = $(window).height();
            body_height = $("header").height() + $(".main_content").height() + $("footer").height();
            if (win_height > body_height) {
                height = win_height - $("header").height() - $("footer").height() - 1;
                $(".main_content").height(height);
            }
        }

        if( window.location.pathname == "/inquery" ) {
            win_height = $(window).height();
            body_height = $("header").height() + $(".main_content").height() + $("footer").height();
            console.log(win_height + "-" + body_height);
            if (win_height > body_height) {
                height = win_height - $("header").height() - $("footer").height() - 1;
                $(".main_content").height(height);
            }
        }


        $('#pedo-visor-app-icon-more').click(function() {
            var hitURL = baseURL + "interest";
            jQuery.ajax({
            type : "POST",
            dataType : "json",
            url : hitURL,
            data : { state: 1, } 
            }).done(function(data){
                
            });
        });
    });

    $(".mobile_head").click(function() {
        if ( $( ".head_menu_extend" ).is( ":hidden" ) ) {
            $( ".head_menu_extend" ).slideDown( "slow" );
        } else {
            $( ".head_menu_extend" ).slideUp( "slow" );
            
        }
    });
});