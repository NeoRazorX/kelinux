function edit_community(idc)
{
    jump2url('/edit_community/'+idc);
}

function remove_community(idc)
{
    if( confirm('Estas completamente seguro de querer eliminar esta comunidad?') )
    {
        document.f_edit_community.remove.value = idc;
        document.f_edit_community.submit();
    }
}
