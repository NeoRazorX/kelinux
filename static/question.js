var req_question;
var v_reload = setTimeout("load_answers()", 500);

function add_reward()
{
    var question_id = document.f_answer.idq.value;
    if(question_id)
    {
        req_question = new XMLHttpRequest();
        if(req_question)
        {
            req_question.onreadystatechange = process_reward;
            req_question.open("POST", "/question_reward", true);
            var formData = new FormData();
            formData.append("idq", question_id);
            req_question.send(formData);
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
    else
    {
        alert("idq no encontrado!");
    }
}

function process_reward()
{
    if(req_question.readyState == 4)
    {
        var messg = req_question.responseText;
        if(messg.substring(0, 2) == 'OK')
        {
            messg2 = messg.split(';');
            var user_points = document.getElementById("current_user_points");
            if(user_points)
            {
                user_points.innerHTML = "Tienes <b>"+messg2[2]+"</b> puntos";
            }
            
            var question_reward = document.getElementById("question_reward");
            if(question_reward)
            {
                question_reward.innerHTML = messg2[1];
            }
        }
        else
        {
            alert(messg);
        }
    }
}

function load_answers()
{
    var question_id = document.f_answer.idq.value;
    if(question_id)
    {
        req_question = new XMLHttpRequest();
        if(req_question)
        {
            req_question.onreadystatechange = process_answers;
            req_question.open("POST", "/answers", true);
            var formData = new FormData();
            formData.append("idq", question_id);
            req_question.send(formData);
            clearTimeout(v_reload);
            v_reload = setTimeout("load_answers()", 300000);
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
    else
    {
        alert("idq no encontrado!");
    }
}

function process_answers()
{
    var question_answers = document.getElementById("question_answers");
    if(req_question.readyState == 4)
    {
        question_answers.innerHTML = req_question.responseText;
    }
    else
    {
        question_answers.innerHTML = 'cargando...';
    }
}

function send_answer()
{
    var question_id = document.f_answer.idq.value;
    if(question_id)
    {
        req_question = new XMLHttpRequest();
        if(req_question)
        {
            req_question.onreadystatechange = process_answers;
            req_question.open("POST", "/answers", true);
            var formData = new FormData();
            formData.append("idq", question_id);
            formData.append("text", document.f_answer.text.value);
            req_question.send(formData);
            document.f_answer.text.value = '';
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
    else
    {
        alert("idq no encontrado!");
    }
}
