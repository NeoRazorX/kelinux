var req;
var recargar = setTimeout("carga_chat_log()", 500);

function carga_chat_log()
{
    req = new XMLHttpRequest();
    if(req)
    {
        req.onreadystatechange = process_chat_log;
        req.open("POST", "/chat_room", true);
        req.send(null);
        document.chat_form.text.focus();
        clearTimeout(recargar);
        recargar = setTimeout("carga_chat_log()", 5000);
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}

function process_chat_log()
{
    var chat_log = document.getElementById("chat_log");
    if(req.readyState == 4)
    {
        chat_log.innerHTML = req.responseText;
    }
    else
    {
        chat_log.innerHTML = 'cargando...';
    }
}

function enviar_chat_msg()
{
    req = new XMLHttpRequest();
    if(req)
    {
        req.onreadystatechange = process_chat_log;
        req.open("POST", "/chat_room", true);
        var formData = new FormData();
        formData.append("text", document.chat_form.text.value);
        req.send(formData);
        document.chat_form.text.value = '';
        document.chat_form.text.focus();
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}
