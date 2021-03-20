function submitOnce(form) {
    if (form.submitted) {
        return false;
    };
    form.submitted = true;
    return true;
}
