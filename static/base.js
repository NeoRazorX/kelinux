function show_popup(idp)
{
    document.getElementById('shadow_box').style.display = 'block';
    tw = window.innerWidth;
    th = window.innerHeight;
    popup = document.getElementById(idp);
    popup.style.left = tw/4+'px';
    popup.style.top = '100px';
    popup.style.display = 'block';
}

function hide_popup(idp)
{
    document.getElementById(idp).style.display = 'none';
    document.getElementById('shadow_box').style.display = 'none';
}

function select_option(idiv, ido, idf)
{
    sdiv = document.getElementById(idiv);
    for (i=0; i<sdiv.childNodes.length; i++)
    {
        if (sdiv.childNodes[i].className == 'option_s')
            sdiv.childNodes[i].className = 'option';
    }
    pdiv = sdiv.parentNode;
    for (i=0; i<pdiv.childNodes.length; i++)
    {
        if (pdiv.childNodes[i].className == 'd_hidden')
            pdiv.childNodes[i].style.display = 'none';
    }
    document.getElementById(ido).className = "option_s";
    document.getElementById(idf).style.display = 'block';
}

function clear_text(item, text)
{
    if(item.value == text)
    {
        item.value = '';
    }
}

var req_create;

function process_create_msg()
{
    var error_create = document.getElementById("error_create");
    if(req_create.readyState == 4)
    {
        error_create.innerHTML = req_create.responseText;
        var jump2link = document.getElementById("jump_2_this_link");
        if(jump2link)
        {
            jump2url( jump2link.href );
        }
    }
    else
    {
        error_create.innerHTML = 'cargando...';
    }
}

function create_community()
{
    req_create = new XMLHttpRequest();
    if(req_create)
    {
        req_create.onreadystatechange = process_create_msg;
        req_create.open("POST", "/create", true);
        var formData = new FormData();
        formData.append("option", "community");
        formData.append("name", document.f_create_community.name.value);
        formData.append("description", document.f_create_community.description.value);
        req_create.send(formData);
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}

function create_question()
{
    req_create = new XMLHttpRequest();
    if(req_create)
    {
        req_create.onreadystatechange = process_create_msg;
        req_create.open("POST", "/create", true);
        var formData = new FormData();
        formData.append("option", "question");
        formData.append("text", document.f_create_question.text.value);
        req_create.send(formData);
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}

function jump2url(url)
{
    window.location.href = url;
}
