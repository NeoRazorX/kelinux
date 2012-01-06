var req_chat;
var v_reload = setTimeout("load_chat_log()", 500);

function load_chat_log()
{
    req_chat = new XMLHttpRequest();
    if(req_chat)
    {
        req_chat.onreadystatechange = process_chat_log;
        req_chat.open("POST", "/chat_room", true);
        req_chat.send(null);
        document.chat_form.text.focus();
        clearTimeout(v_reload);
        v_reload = setTimeout("load_chat_log()", 15000);
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}

function process_chat_log()
{
    var chat_log = document.getElementById("chat_log");
    if(req_chat.readyState == 4)
    {
        chat_log.innerHTML = req_chat.responseText;
    }
    else
    {
        chat_log.innerHTML = '<div class="message">cargando...</div>';
    }
}

function send_chat_msg()
{
    req_chat = new XMLHttpRequest();
    if(req_chat)
    {
        req_chat.onreadystatechange = process_chat_log;
        req_chat.open("POST", "/chat_room", true);
        var formData = new FormData();
        formData.append("text", document.chat_form.text.value);
        req_chat.send(formData);
        document.chat_form.text.value = '';
        document.chat_form.text.focus();
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}
