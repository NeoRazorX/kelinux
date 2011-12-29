function mostrar_popup(idp)
{
    document.getElementById('caja_sombra').style.display = 'block';
    tw = window.innerWidth;
    th = window.innerHeight;
    popup = document.getElementById(idp);
    popup.style.left = tw/4+'px';
    popup.style.top = '100px';
    popup.style.display = 'block';
}

function ocultar_popup(idp)
{
    document.getElementById(idp).style.display = 'none';
    document.getElementById('caja_sombra').style.display = 'none';
}

function seleccionar_opcion(idiv, ido, idf)
{
    sdiv = document.getElementById(idiv);
    for (i=0; i<sdiv.childNodes.length; i++)
    {
        if (sdiv.childNodes[i].className == 'opcion_s')
            sdiv.childNodes[i].className = 'opcion';
    }
    pdiv = sdiv.parentNode;
    for (i=0; i<pdiv.childNodes.length; i++)
    {
        if (pdiv.childNodes[i].className == 'oculto')
            pdiv.childNodes[i].style.display = 'none';
    }
    document.getElementById(ido).className = "opcion_s";
    document.getElementById(idf).style.display = 'block';
}
