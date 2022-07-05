var utc2local = function (utc_time, format) {
    if (!format)
        format = 'YYYY-MM-DD HH:mm:ss';
    var localTime = moment.utc(utc_time).toDate();
    return moment(localTime).format(format);
};

var local2utc = function(localtime, format){
    if (!format)
        format = 'YYYY-MM-DD HH:mm:ss';
    var utc_time = moment(localtime).utc();
    return utc_time.format(format);
};
var diff_time = function (start, end) {
    var start = moment(start),
        end = moment(end);
    var duration = moment.duration(end.diff(start));
    return duration.hours() > 0 ? (duration.hours() + "h ") : "" + duration.minutes() + "' " + duration.seconds() + '"';
};

var diff_time_second = function (start, end) {
    var start = moment(start),
        end = moment(end);
    var duration = moment.duration(end.diff(start));
    return duration.asSeconds();
};

var number_format = function(number, size){
    return parseInt(number * Math.pow(10,size))/Math.pow(10,size);
};

function view_head_menu(){
    if($(".head_menu_extend").css("display") == "none"){
        $(".head_menu_extend").css("display","block")
    }else{
        $(".head_menu_extend").css("display","none")
    }
}

$.validator.addMethod("greaterThan", function(value, element, params) {

    if (!/Invalid|NaN/.test(new Date(value))) {
        return new Date(value) > new Date($(params).val());
    }
    return isNaN(value) && isNaN($(params).val())
        || (Number(value) > Number($(params).val()));
},'Must be greater than {0}.');

var error_msg = function(error){
    var msg ={
        "default":"処理中にエラーが発生しました。",
        "ERR_INVALID_EMAIL":"メールアドレスが正確ではないです。",
        "ERR_USERNAME_ALREADY_EXISTS":"ユーザーのIDがすでに存在します。",
        "ERR_EMAIL_ALREADY_EXISTS":"メールアドレスがすでに存在します。",
        "ERR_USER_CREATE":"ユーザー登録エラーです。",
        "ERR_INVALID_USER":"ユーザー情報が正確ではありません。",
        "ERR_PROFILE_SAVE":"ユーザープロフィール保存エラーです。",
        "ERR_EMAIL_SAVE":"メールアドレス保存エラーです。",
        "ERR_NO_PROFILE":"ユーザー情報はありません。",
        "ERR_INVALID_BIRTHDAY":"日付形式の誤りです。",
        "ERR_NO_USER":"ユーザーが存在しません。",
        "ERR_SEND_MAIL":"メールを送るのが失敗しました。",
        "ERR_EMAIL_VERIFY":"メールアドレスが正確ではありません。",
        "ERR_EMAIL_VERIFICATION":"メールアドレスが正確ではありません。",
        "ERR_PASSWORD_SAVE":"パスワード設定でエラーが発生しました。",
        "ERR_INVALID_PASSWORD":"パスワードが正確ではありません。",
        "ERR_NO_DATA":"データがありません。",
        "ERR_WEIGHTDATA_SAVE":"処理中にエラーが発生しました。",
        "ERR_NO_ID":"IDが存在しません。",
        "ERR_NO_DATE":"日付が存在しません。",
        "ERR_EXIST_DATA":"すでにデータが存在します。",
        "ERR_NO_BED_TIME":"就寝時間を正確に入力してください。",
        "ERR_NO_WAKEUP_TIME":"起床時間を正確に入力してください。",
        "ERR_TIME_FORMAT":"時間の形式が正確ではありません。",
        "ERR_INVALID_TIME":"時間の形式が正確ではありません。",
        "ERR_NOT_EXIST":"データがありません。",
    };
    if (error && msg[error]){
            return msg[error];
    }else{
        return msg.default;
    }
};