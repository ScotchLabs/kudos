function submit_vote() {
    $("#nomid").val(this.getAttribute("nomid"));
    $.post("/submit_vote", $("#voteform").serialize(), function (text) {
        let data = JSON.parse(text);
        if (data["success"] >= 1) {
            let no_vote_id = data["no_vote"];
            $(`#nom${no_vote_id}`).removeClass("vote");
            if (data["success"] === 2) {
                let vote_id = data["vote"];
                $(`#nom${vote_id}`).addClass("vote");
            };
        } else {
            alert(data["message"]);
        };
    }).fail(function() {
        alert("An error occured");
    });
    return false;
};

$(".vote-button").click(submit_vote)
