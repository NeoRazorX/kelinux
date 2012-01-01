var req_question;

function add_reward(idq)
{
    req_question = new XMLHttpRequest();
    if(req_question)
    {
        req_question.onreadystatechange = process_reward;
        req_question.open("POST", "/question_reward", true);
        var formData = new FormData();
        formData.append("idq", idq);
        req_question.send(formData);
    }
    else
    {
        alert("Imposible crear la peticion!");
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
