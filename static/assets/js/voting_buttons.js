function submit_vote() {
    $("#nomid").val(this.getAttribute("nomid"));
    $.post("/submit_vote", $("#voteform").serialize(), function (text) {
        try {
            let data = JSON.parse(text);
            if (data["success"] >= 1) {
                let no_votes = data["no_vote"];
                for (var i = 0; i < no_votes.length; i++) {
                    $(`#nom${no_votes[i]}`).removeClass("vote");;
                };
                if (data["success"] === 2) {
                    let vote_id = data["vote"];
                    $(`#nom${vote_id}`).addClass("vote");
                };
            } else {
                alert(data["message"]);
            };
        } catch(err) {
            alert(`An error occured: ${err}`);
        };
    }).fail(function() {
        alert("An error occured");
    });
    return false;
};

$(".vote-button").click(submit_vote)
