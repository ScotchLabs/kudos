function submit_vote(click_id) {
    $.post('/submit_vote', {nom: click_id}, function (text) {
        let data = JSON.parse(text);
        if (data["success"] >= 1) {
            let no_vote_id = data["no_vote"];
            $("a[name=nom" + no_vote_id + "]").css("background-color", "transparent");
            if (data["success"] === 2) {
                let vote_id = data["vote"];
                $("a[name=nom" + vote_id + "]").css("background-color", "lightgreen");
            };
        } else {
            alert(data["message"]);
        }
    });
    return false;
}
