var req_reward = false;
var req_question = false;
var req_vote_answer = false;
var v_reload;
var answer_order = 'grade';

function add_reward(idq)
{
    if(!req_reward)
    {
        if(window.XMLHttpRequest)
            req_reward = new XMLHttpRequest();
        else
            req_reward = new ActiveXObject("Microsoft.XMLHTTP");
        
        if(req_reward)
        {
            req_reward.onreadystatechange = process_reward;
            req_reward.open("POST", "/question_reward", true);
            var formData = new FormData();
            formData.append("idq", idq);
            req_reward.send(formData);
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
}

function process_reward()
{
    if(req_reward.readyState == 4)
    {
        var messg = req_reward.responseText;
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
        req_reward = false
    }
}

function load_answers()
{
    if(!req_question)
    {
        var question_id = document.f_answer.idq.value;
        if(question_id)
        {
            if(window.XMLHttpRequest)
                req_question = new XMLHttpRequest();
            else
                req_question = new ActiveXObject("Microsoft.XMLHTTP");
            
            if(req_question)
            {
                req_question.onreadystatechange = process_answers;
                req_question.open("POST", "/answers", true);
                var formData = new FormData();
                formData.append("idq", question_id);
                formData.append("order", answer_order);
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
}

function set_answer_order(order)
{
    answer_order = order;
    if(answer_order == 'grade')
    {
        document.getElementById("answers_order_grade").setAttribute("class", "selected");
        document.getElementById("answers_order_normal").setAttribute("class", "");
    }
    else
    {
        document.getElementById("answers_order_normal").setAttribute("class", "selected");
        document.getElementById("answers_order_grade").setAttribute("class", "");
    }
    load_answers();
}

function process_answers()
{
    var question_answers = document.getElementById("question_answers");
    if(req_question.readyState == 4)
    {
        question_answers.innerHTML = req_question.responseText;
        req_question = false;
    }
    else
    {
        question_answers.innerHTML = '<div class="message">cargando...</div>';
    }
}

function send_answer(idq)
{
    if(window.XMLHttpRequest)
        req_question = new XMLHttpRequest();
    else
        req_question = new ActiveXObject("Microsoft.XMLHTTP");
    
    if(req_question)
    {
        req_question.onreadystatechange = process_answers;
        req_question.open("POST", "/answers", true);
        var formData = new FormData();
        formData.append("idq", idq);
        formData.append("text", document.f_answer.text.value);
        req_question.send(formData);
        document.f_answer.text.value = '';
    }
    else
    {
        alert("Imposible crear la peticion!");
    }
}

function mark_solution(ida)
{
    if(!req_vote_answer)
    {
        if(window.XMLHttpRequest)
            req_vote_answer = new XMLHttpRequest();
        else
            req_vote_answer = new ActiveXObject("Microsoft.XMLHTTP");
        
        if(req_vote_answer)
        {
            req_vote_answer.onreadystatechange = process_answer_solution;
            req_vote_answer.open("POST", "/vote_answers", true);
            var formData = new FormData();
            formData.append("ida", ida);
            formData.append("option", "solution");
            req_vote_answer.send(formData);
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
}

function vote_answer(ida, positive)
{
    if(!req_vote_answer)
    {
        if(window.XMLHttpRequest)
            req_vote_answer = new XMLHttpRequest();
        else
            req_vote_answer = new ActiveXObject("Microsoft.XMLHTTP");
        
        if(req_vote_answer)
        {
            req_vote_answer.onreadystatechange = process_answer_vote;
            req_vote_answer.open("POST", "/vote_answers", true);
            var formData = new FormData();
            formData.append("ida", ida);
            if(positive)
                formData.append("option", "positive");
            else
                formData.append("option", "negative");
            req_vote_answer.send(formData);
        }
        else
        {
            alert("Imposible crear la peticion!");
        }
    }
}

function process_answer_vote()
{
    if(req_vote_answer.readyState == 4)
    {
        var messg = req_vote_answer.responseText;
        if(messg.substring(0, 2) == 'OK')
        {
            messg2 = messg.split(';');
            var answer_grade = document.getElementById("answer_grade_"+messg2[1]);
            if(answer_grade)
            {
                answer_grade.innerHTML = messg2[2];
            }
            
            var user_points = document.getElementById("current_user_points");
            if(user_points)
            {
                user_points.innerHTML = "Tienes <b>"+messg2[3]+"</b> puntos";
            }
        }
        else
        {
            alert(messg);
        }
        req_vote_answer = false;
    }
}

function process_answer_solution()
{
    if(req_vote_answer.readyState == 4)
    {
        var messg = req_vote_answer.responseText;
        if(messg.substring(0, 2) == 'OK')
        {
            window.location.reload();
        }
        else
        {
            alert(messg);
        }
        req_vote_answer = false;
    }
}

function edit_question(idq)
{
    jump2url('/edit_question/'+idq);
}

function remove_question(idq)
{
    if( confirm('Estas completamente seguro de querer eliminar esta pregunta?') )
    {
        document.f_edit_question.remove.value = idq;
        document.f_edit_question.submit();
    }
}
